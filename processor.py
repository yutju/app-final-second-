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

# 🚀 중요: 여기서 'from processor import PDFProcessor' 구문을 절대 넣지 마세요!
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
        """무손실 최적화를 통한 고화질 이미지 바이트 추출"""
        with PILImage.open(wm_image_path) as img:
            if img.mode not in ("RGBA", "RGB"):
                img = img.convert("RGBA")
            buf = BytesIO()
            # 🚀 optimize=True로 품질 확보
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

        pos_map = {
            "center": (page_width / 2, page_height / 2),
            "top-left": (page_width * 0.2, page_height * 0.85),
            "top-right": (page_width * 0.8, page_height * 0.85),
            "bottom-left": (page_width * 0.2, page_height * 0.15),
            "bottom-right": (page_width * 0.8, page_height * 0.15),
        }
        x, y = pos_map.get(wm_position, (page_width / 2, page_height / 2))
        opacity = max(0.1, min(wm_opacity, 1.0))

        if wm_type == "image" and wm_image_bytes:
            try:
                logo = ImageReader(BytesIO(wm_image_bytes))
                s = wm_size * mm
                is_rgba = self._is_rgba_png(wm_image_bytes)
                mask = 'auto' if is_rgba else None
                can.saveState()
                can.translate(x, y)
                can.rotate(wm_rotation)
                can.setFillAlpha(opacity)
                # 🚀 anchor='c' 옵션으로 뭉개짐 방지
                can.drawImage(logo, -s/2, -s/2, width=s, height=s, mask=mask, preserveAspectRatio=True, anchor='c')
                can.restoreState()
            except Exception as e:
                logger.error(f"[WM] 이미지 그리기 실패: {e}")

        elif wm_type == "text" and wm_text:
            can.saveState()
            can.setFont("Helvetica-Bold", wm_size)
            can.setFillAlpha(opacity)
            can.translate(x, y); can.rotate(wm_rotation)
            can.drawCentredString(0, 0, wm_text)
            can.restoreState()

        if use_page_number:
            can.setFont("Helvetica", 10)
            can.setFillAlpha(0.5)
            can.drawCentredString(page_width / 2, 10 * mm, f"- Page {page_num} / {total_pages} -")

        can.showPage()
        can.save()
        packet.seek(0)
        return packet

    def process_merge(self, input_paths, output_path, wm_type, wm_text, wm_image_path, wm_position, wm_size, wm_opacity, wm_rotation, user_pw, use_page_number):
        fragments = [self._convert_to_pdf_fragment(p) for p in input_paths if p]
        fragments = [f for f in fragments if f]
        if not fragments: raise ValueError("변환된 PDF가 없습니다.")

        merged_raw = os.path.join(self.temp_dir, f"raw_{uuid.uuid4()}.pdf")
        subprocess.run(["gs", "-sDEVICE=pdfwrite", "-dCompatibilityLevel=1.4", "-dNOPAUSE", "-dQUIET", "-dBATCH", f"-sOutputFile={merged_raw}"] + fragments, check=True)

        wm_image_bytes = None
        if wm_type == "image" and wm_image_path and os.path.exists(wm_image_path):
            wm_image_bytes = self._prepare_wm_image_bytes(wm_image_path)

        with pikepdf.open(merged_raw) as pdf:
            for i, page in enumerate(pdf.pages):
                if "/Group" in page: del page["/Group"]
                pw = float(page.MediaBox[2]); ph = float(page.MediaBox[3])
                wm_packet = self._draw_watermark_layer(pw, ph, wm_type, wm_text, wm_image_bytes, wm_position, wm_size, wm_opacity, wm_rotation, i+1, len(pdf.pages), use_page_number)
                with pikepdf.open(wm_packet) as wm_pdf:
                    page.add_overlay(wm_pdf.pages[0])
                wm_packet.close()

            if user_pw:
                pdf.save(output_path, encryption=pikepdf.Encryption(user=user_pw, owner=str(uuid.uuid4()), R=4))
            else:
                pdf.save(output_path, static_id=True)

        for f in fragments: os.remove(f)
        if os.path.exists(merged_raw): os.remove(merged_raw)
