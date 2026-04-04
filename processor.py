import os
import time
import shutil
import uuid
import logging
from io import BytesIO
from PIL import Image
from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import pikepdf

from converter import run_libreoffice, SUPPORTED_IMAGE_EXTS, SUPPORTED_DOC_EXTS

logger = logging.getLogger("SixSense-Converter")

FONT_NAME = "NanumGothic"
FONT_PATH = '/usr/share/fonts/truetype/nanum/NanumGothic.ttf'

def register_fonts():
    try:
        if os.path.exists(FONT_PATH):
            pdfmetrics.registerFont(TTFont(FONT_NAME, FONT_PATH))
            return True
    except: return False
    return False

HAS_NANUM = register_fonts()

class PDFProcessor:
    def __init__(self, temp_dir):
        self.temp_dir = temp_dir

    def _convert_to_pdf_fragment(self, input_path):
        ext = input_path.rsplit('.', 1)[-1].lower()
        tmp_pdf = os.path.join(self.temp_dir, f"frag_{uuid.uuid4()}.pdf")

        # 1. 이미지 처리 (Pillow)
        if ext in SUPPORTED_IMAGE_EXTS:
            with Image.open(input_path) as img:
                if img.mode != "RGB":
                    img = img.convert("RGB")
                img.save(tmp_pdf, "PDF")
            return tmp_pdf

        # 2. 문서 처리 (LibreOffice) — converter.run_libreoffice 공용 함수 사용
        if ext not in SUPPORTED_DOC_EXTS:
            raise ValueError(f"지원하지 않는 확장자입니다: .{ext}")

        ts = str(int(time.time() * 1000))
        profile_dir = os.path.join(self.temp_dir, f"env_{ts}_{uuid.uuid4().hex[:6]}")
        os.makedirs(profile_dir, exist_ok=True)

        # TXT 파일 인코딩 보정
        if ext == "txt":
            with open(input_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
            with open(input_path, "w", encoding="utf-8") as f:
                f.write(content)

        env = os.environ.copy()
        env.update({
            "HOME": profile_dir,
            "LANG": "ko_KR.UTF-8",
            "LC_ALL": "ko_KR.UTF-8",
            "LANGUAGE": "ko_KR:ko",
            "SAL_USE_VCLPLUGIN": "gen",
            "SAL_VCL_QT5_USE_CAIRO": "1",
            "FONTCONFIG_PATH": "/etc/fonts",
        })

        try:
            run_libreoffice(input_path, profile_dir, env)
            gen_pdf = os.path.join(
                profile_dir,
                f"{os.path.basename(input_path).rsplit('.', 1)[0]}.pdf"
            )
            if os.path.exists(gen_pdf):
                shutil.move(gen_pdf, tmp_pdf)
                return tmp_pdf
        finally:
            shutil.rmtree(profile_dir, ignore_errors=True)

        return None

    # [메인] 다중 파일 병합 실행 함수
    def process_merge(
        self,
        input_paths,
        output_path,
        wm_type="none",
        wm_text="SIX SENSE",
        wm_image_path=None,
        wm_position="center",   # center | top-left | top-right | bottom-left | bottom-right
        wm_size=60,             # 텍스트: 폰트 크기(pt) / 이미지: 단축변 길이(mm)
        wm_opacity=0.3,         # 0.0 ~ 1.0
        wm_rotation=45,         # 회전각 (도)
    ):
        fragments = []
        try:
            # 1. 모든 파일을 PDF 조각으로 변환
            for path in input_paths:
                frag = self._convert_to_pdf_fragment(path)
                if frag: fragments.append(frag)

            if not fragments:
                raise Exception("변환할 수 있는 파일이 없습니다.")

            # 2. 고성능 병합 (pikepdf 사용)
            with pikepdf.new() as merged:
                for frag in fragments:
                    with pikepdf.open(frag) as src:
                        merged.pages.extend(src.pages)

                if not wm_type or wm_type == "none":
                    merged.save(output_path)
                    return

                intermediate_pdf = os.path.join(self.temp_dir, f"merged_{uuid.uuid4()}.pdf")
                merged.save(intermediate_pdf)

            # 3. 병합된 PDF에 워터마크 입히기
            reader = PdfReader(intermediate_pdf)
            writer = PdfWriter()
            active_font = FONT_NAME if HAS_NANUM else "Helvetica"

            self.add_custom_watermark(
                reader, writer, active_font,
                wm_type, wm_text, wm_image_path,
                wm_position, wm_size, wm_opacity, wm_rotation,
            )

            with open(output_path, "wb") as f:
                writer.write(f)

            if os.path.exists(intermediate_pdf): os.remove(intermediate_pdf)

        finally:
            for frag in fragments:
                if os.path.exists(frag): os.remove(frag)

    # 워터마크 위치/크기/투명도/회전 커스텀 지원
    def add_custom_watermark(
        self, reader, writer, active_font,
        wm_type, wm_text, wm_image_path,
        wm_position="center",
        wm_size=60,
        wm_opacity=0.3,
        wm_rotation=45,
    ):
        width, height = A4

        # position 문자열 → (x, y) 좌표 변환
        POSITION_MAP = {
            "center":       (width / 2,        height / 2),
            "top-left":     (width * 0.2,      height * 0.8),
            "top-right":    (width * 0.8,      height * 0.8),
            "bottom-left":  (width * 0.2,      height * 0.2),
            "bottom-right": (width * 0.8,      height * 0.2),
        }
        x, y = POSITION_MAP.get(wm_position, POSITION_MAP["center"])
        opacity = max(0.0, min(1.0, wm_opacity))  # 0~1 클램프

        for i, page in enumerate(reader.pages):
            packet = BytesIO()
            can = canvas.Canvas(packet, pagesize=A4)

            if wm_type == "text" and wm_text:
                can.saveState()
                can.setFont(active_font, wm_size)
                can.setFillColorRGB(0.7, 0.7, 0.7, alpha=opacity)
                can.translate(x, y)
                can.rotate(wm_rotation)
                can.drawCentredString(0, 0, wm_text)
                can.restoreState()

            elif wm_type == "image" and wm_image_path:
                img_side = wm_size * mm
                can.saveState()
                can.translate(x, y)
                can.rotate(wm_rotation)
                can.setFillAlpha(opacity)
                can.drawImage(
                    wm_image_path,
                    -img_side / 2, -img_side / 2,
                    width=img_side, height=img_side,
                    mask='auto', preserveAspectRatio=True,
                )
                can.restoreState()

            # 하단 페이지 정보
            can.setFont(active_font, 10)
            can.setFillColorRGB(0.5, 0.5, 0.5, alpha=0.5)
            can.drawRightString(width - 20, 30, f"SixSense Secured | Page {i+1} / {len(reader.pages)}")

            can.save()
            packet.seek(0)
            overlay = PdfReader(packet)
            page.merge_page(overlay.pages[0])
            writer.add_page(page)
