import os
import uuid
import subprocess
import shutil
import logging
from io import BytesIO
import pikepdf
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from PIL import Image as PILImage

# 🚀 중요: 순환 참조 방지를 위해 내부에서 PDFProcessor를 임포트하지 마세요.
from converter import run_libreoffice, SUPPORTED_IMAGE_EXTS

logger = logging.getLogger("SixSense-Processor")

class PDFProcessor:
    def __init__(self, temp_dir):
        self.temp_dir = temp_dir

    def _convert_to_pdf_fragment(self, input_path):
        ext = input_path.split('.')[-1].lower()
        tmp_pdf = os.path.join(self.temp_dir, f"frag_{uuid.uuid4()}.pdf")

        if ext in SUPPORTED_IMAGE_EXTS:
            with PILImage.open(input_path) as img:
                img.convert("RGB").save(tmp_pdf, "PDF")
            return tmp_pdf

        profile_dir = os.path.join(self.temp_dir, f"env_{uuid.uuid4().hex[:6]}")
        os.makedirs(profile_dir, exist_ok=True)

        try:
            env = os.environ.copy()
            env.update({"HOME": profile_dir, "LANG": "ko_KR.UTF-8"})
            run_libreoffice(input_path, profile_dir, env)
            gen_pdf = os.path.join(profile_dir, f"{os.path.basename(input_path).rsplit('.', 1)[0]}.pdf")
            if os.path.exists(gen_pdf):
                shutil.move(gen_pdf, tmp_pdf)
                return tmp_pdf
            return None
        finally:
            shutil.rmtree(profile_dir, ignore_errors=True)

    def _prepare_wm_image_bytes(self, wm_image_path: str) -> bytes:
        """
        🔥 [해결책 1] 이미지 해상도 표준화
        원본 파일의 크기에 상관없이 512px 규격으로 리사이징하여 
        기준점을 통일합니다. (파일마다 크기가 들쑥날쑥한 현상 방지)
        """
        with PILImage.open(wm_image_path) as img:
            if img.mode not in ("RGBA", "RGB"):
                img = img.convert("RGBA")
            
            base_size = 512
            w, h = img.size
            scale = base_size / max(w, h)
            new_size = (int(w * scale), int(h * scale))
            img = img.resize(new_size, PILImage.LANCZOS)
            
            buf = BytesIO()
            img.save(buf, format="PNG", optimize=True)
            return buf.getvalue()

    def _is_rgba_png(self, image_bytes: bytes) -> bool:
        try:
            return image_bytes[25] == 6
        except:
            return False

    def _draw_watermark_layer(self, page_width, page_height, wm_type, wm_text, wm_image_bytes, wm_position, wm_size, wm_opacity, wm_rotation, page_num, total_pages, use_page_number):
        packet = BytesIO()
        can = canvas.Canvas(packet, pagesize=(page_width, page_height))

        # 🚀 [해결책 2] 좌표 비율 동기화
        # 웹 미리보기 가이드의 여백 비율(15%, 85%)을 PDF pt 좌표계에 그대로 이식합니다.
        pos_map = {
            "center": (page_width / 2, page_height / 2),
            "top-left": (page_width * 0.15, page_height * 0.9),     
            "top-right": (page_width * 0.85, page_height * 0.9),
            "bottom-left": (page_width * 0.15, page_height * 0.1),
            "bottom-right": (page_width * 0.85, page_height * 0.1),
        }
        x, y = pos_map.get(wm_position, (page_width / 2, page_height / 2))
        opacity = max(0.1, min(wm_opacity, 1.0))

        if wm_type == "image" and wm_image_bytes:
            try:
                logo = ImageReader(BytesIO(wm_image_bytes))
                
                # 🔥 [해결책 3] 상대적 비율(%) 기반 크기 계산
                # wm_size(사용자가 입력한 %)를 실제 페이지 너비(page_width)의 비율로 변환합니다.
                # 웹의 가이드 박스 너비 대비 로고 크기 비율이 PDF에서도 1:1로 유지됩니다.
                s = page_width * (wm_size / 100) 
                
                is_rgba = self._is_rgba_png(wm_image_bytes)
                mask = 'auto' if is_rgba else None
                can.saveState()
                can.translate(x, y)
                can.rotate(wm_rotation)
                can.setFillAlpha(opacity)
                
                # anchor='c'를 통해 이미지 중심을 정확히 고정
                can.drawImage(logo, -s/2, -s/2, width=s, height=s, mask=mask, preserveAspectRatio=True, anchor='c')
                can.restoreState()
            except Exception as e:
                logger.error(f"[WM] 이미지 그리기 실패: {e}")

        elif wm_type == "text" and wm_text:
            can.saveState()
            # 텍스트 역시 페이지 너비 대비 비율로 폰트 크기 결정
            font_size = page_width * (wm_size / 100)
            can.setFont("Helvetica-Bold", font_size) 
            can.setFillColorRGB(0.31, 0.27, 0.9) # 웹 Indigo-600 색상
            can.setFillAlpha(opacity)
            can.translate(x, y); can.rotate(wm_rotation)
            can.drawCentredString(0, 0, wm_text)
            can.restoreState()

        if use_page_number:
            can.setFont("Helvetica", 10)
            can.setFillAlpha(0.5)
            can.drawCentredString(page_width / 2, 30, f"- Page {page_num} / {total_pages} -")

        can.showPage()
        can.save()
        packet.seek(0)
        return packet

    def process_merge(self, input_paths, output_path, wm_type, wm_text, wm_image_path, wm_position, wm_size, wm_opacity, wm_rotation, user_pw, use_page_number):
        fragments = [self._convert_to_pdf_fragment(p) for p in input_paths if p]
        fragments = [f for f in fragments if f]
        if not fragments: raise ValueError("변환된 PDF가 없습니다.")

        # Ghostscript를 통한 표준화 병합 (압축 최적화)
        merged_raw = os.path.join(self.temp_dir, f"raw_{uuid.uuid4()}.pdf")
        subprocess.run(["gs", "-sDEVICE=pdfwrite", "-dCompatibilityLevel=1.4", "-dNOPAUSE", "-dQUIET", "-dBATCH", f"-sOutputFile={merged_raw}"] + fragments, check=True)

        wm_image_bytes = None
        if wm_type == "image" and wm_image_path and os.path.exists(wm_image_path):
            wm_image_bytes = self._prepare_wm_image_bytes(wm_image_path)

        # pikepdf를 통한 워터마크 레이어 오버레이 합성
        with pikepdf.open(merged_raw) as pdf:
            total_count = len(pdf.pages)
            for i, page in enumerate(pdf.pages):
                if "/Group" in page: del page["/Group"]
                
                pw = float(page.MediaBox[2])
                ph = float(page.MediaBox[3])
                
                # wm_size는 이제 '숫자'가 아닌 '비중(%)'으로 전달됩니다.
                wm_packet = self._draw_watermark_layer(pw, ph, wm_type, wm_text, wm_image_bytes, wm_position, float(wm_size), wm_opacity, wm_rotation, i+1, total_count, use_page_number)
                
                with pikepdf.open(wm_packet) as wm_pdf:
                    page.add_overlay(wm_pdf.pages[0])
                wm_packet.close()

            if user_pw:
                pdf.save(output_path, encryption=pikepdf.Encryption(user=user_pw, owner=str(uuid.uuid4()), R=4))
            else:
                pdf.save(output_path, static_id=True)

        # 임시 파일 정리
        for f in fragments: os.remove(f)
        if os.path.exists(merged_raw): os.remove(merged_raw)
