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
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from PIL import Image as PILImage

from converter import run_libreoffice, SUPPORTED_IMAGE_EXTS

logger = logging.getLogger("SixSense-Processor")

# 폰트 등록 안전 장치
try:
    font_path = "/usr/share/fonts/truetype/nanum/NanumGothicBold.ttf"
    if os.path.exists(font_path):
        pdfmetrics.registerFont(TTFont("NanumGothicBold", font_path))
        FONT_NAME = "NanumGothicBold"
    else:
        FONT_NAME = "Helvetica-Bold"
except:
    FONT_NAME = "Helvetica-Bold"

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
        try: return image_bytes[25] == 6
        except: return False

    def _draw_watermark_layer(self, page_width, page_height, wm_type, wm_text, wm_image_bytes, wm_position, wm_size, wm_opacity, wm_rotation, page_num, total_pages, use_page_number):
        packet = BytesIO()
        can = canvas.Canvas(packet, pagesize=(page_width, page_height))
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
                s = page_width * (wm_size / 100) 
                is_rgba = self._is_rgba_png(wm_image_bytes)
                mask = 'auto' if is_rgba else None
                can.saveState()
                can.translate(x, y); can.rotate(wm_rotation); can.setFillAlpha(opacity)
                can.drawImage(logo, -s/2, -s/2, width=s, height=s, mask=mask, preserveAspectRatio=True, anchor='c')
                can.restoreState()
            except Exception as e:
                logger.error(f"[WM] 이미지 그리기 실패: {e}")

        elif wm_type == "text" and wm_text:
            try:
                can.saveState()
                font_size = page_width * (wm_size / 100) * 0.8 # 크기 상향
                can.setFont(FONT_NAME, font_size) 
                can.setFillColorRGB(0.4, 0.4, 0.4) # 회색
                can.setFillAlpha(opacity)
                can.translate(x, y); can.rotate(wm_rotation)
                can.drawCentredString(0, 0, str(wm_text))
                can.restoreState()
            except Exception as e:
                logger.error(f"[WM] 텍스트 그리기 실패: {e}")

        if use_page_number:
            can.setFont("Helvetica", 10); can.setFillAlpha(0.5)
            can.drawCentredString(page_width / 2, 30, f"- Page {page_num} / {total_pages} -")

        can.showPage(); can.save(); packet.seek(0)
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
            tp = len(pdf.pages)
            for i, page in enumerate(pdf.pages):
                if "/Group" in page: del page["/Group"]
                pw = float(page.MediaBox[2]); ph = float(page.MediaBox[3])
                wm_packet = self._draw_watermark_layer(pw, ph, wm_type, wm_text, wm_image_bytes, wm_position, float(wm_size), wm_opacity, wm_rotation, i+1, tp, use_page_number)
                with pikepdf.open(wm_packet) as wm_pdf:
                    page.add_overlay(wm_pdf.pages[0])
                wm_packet.close()
            if user_pw:
                pdf.save(output_path, encryption=pikepdf.Encryption(user=user_pw, owner=str(uuid.uuid4()), R=4))
            else:
                pdf.save(output_path, static_id=True)
        for f in fragments: os.remove(f)
        if os.path.exists(merged_raw): os.remove(merged_raw)
