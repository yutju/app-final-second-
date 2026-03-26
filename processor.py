import os
import subprocess
import time
import shutil
import random
import logging
from io import BytesIO
from docx import Document
from PIL import Image
from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import pikepdf

logger = logging.getLogger("SixSense-Converter")

# 폰트 등록 (실패 시 대비 폴백 로직)
FONT_NAME = "NanumGothic"
FONT_PATH = '/usr/share/fonts/truetype/nanum/NanumGothic.ttf'

def register_fonts():
    try:
        if os.path.exists(FONT_PATH):
            pdfmetrics.registerFont(TTFont(FONT_NAME, FONT_PATH))
            return True
    except:
        return False
    return False

HAS_NANUM = register_fonts()

class PDFProcessor:
    def __init__(self, input_path, output_path, temp_dir):
        self.input_path = input_path
        self.output_path = output_path
        self.temp_dir = temp_dir
        self.ext = input_path.rsplit('.', 1)[-1].lower()
        self.base_pdf = os.path.join(temp_dir, f"base_{int(time.time()*1000)}.pdf")

    def convert_to_pdf(self):
        # 이미지 파일 처리
        if self.ext in ["png", "jpg", "jpeg", "bmp"]:
            with Image.open(self.input_path) as img:
                if img.mode != "RGB": img = img.convert("RGB")
                img.save(self.base_pdf, "PDF")
            return

        ts = str(int(time.time() * 1000))
        profile_dir = os.path.join(self.temp_dir, f"env_{ts}")
        os.makedirs(profile_dir, exist_ok=True)
        user_profile = os.path.join(profile_dir, "lo_profile")
        safe_input = os.path.join(profile_dir, f"input.{self.ext}")
        shutil.copy2(self.input_path, safe_input)

        env = os.environ.copy()
        env.update({
            "HOME": profile_dir,
            "LANG": "ko_KR.UTF-8",
            "LC_ALL": "ko_KR.UTF-8",
            "SAL_USE_VCLPLUGIN": "gen",
            # 🔥 핵심: 표가 깨지는 주범인 그래픽 가속을 완전히 끕니다.
            "SAL_DISABLE_OPENCL": "1",
            "SAL_DISABLE_GL": "1",
            "JAVA_HOME": ""
        })

        display_num = random.randint(200, 299)
        # Xvfb 옵션에 RENDER 확장 추가하여 표 선 렌더링 지원
        xvfb_cmd = ["Xvfb", f":{display_num}", "-screen", "0", "1920x1080x24", "-ac", "+extension", "GLX", "+extension", "RENDER"]

        xvfb_proc = None
        try:
            xvfb_proc = subprocess.Popen(xvfb_cmd, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            time.sleep(2)
            env["DISPLAY"] = f":{display_num}"

            # 🔥 표 형식을 강제로 유지하게 만드는 마법의 필터 옵션
            # PDF/A-1b 표준과 Tagged PDF 구조를 강제하여 표가 텍스트로 분해되는 것을 막습니다.
            pdf_filter = 'pdf:writer_pdf_Export:{"SelectPdfVersion":{"type":"long","value":"1"},"ExportFormFields":{"type":"boolean","value":"true"},"IsSkipEmptyPages":{"type":"boolean","value":"false"}}'

            lo_cmd = [
                "libreoffice", f"-env:UserInstallation=file://{user_profile}",
                "--headless", "--invisible", "--nodefault", "--nofirststartwizard",
                "--nolockcheck", "--nologo", "--norestore",
                "--convert-to", pdf_filter,
                "--outdir", profile_dir, safe_input
            ]

            result = subprocess.run(lo_cmd, env=env, capture_output=True, text=True, timeout=120)
            if result.returncode != 0:
                logger.error(f"LO Error: {result.stderr}")
                raise RuntimeError("LibreOffice 변환 실패")

            gen_pdf = os.path.join(profile_dir, "input.pdf")
            if os.path.exists(gen_pdf):
                shutil.move(gen_pdf, self.base_pdf)
            else:
                raise FileNotFoundError("PDF 결과물 생성 실패")

        finally:
            if xvfb_proc:
                xvfb_proc.terminate()
                xvfb_proc.wait()
            shutil.rmtree(profile_dir, ignore_errors=True)

    def add_overlays_and_bookmarks(self, watermark_text="SIX SENSE"):
        reader = PdfReader(self.base_pdf)
        writer = PdfWriter()
        active_font = FONT_NAME if HAS_NANUM else "Helvetica"

        for i, page in enumerate(reader.pages):
            packet = BytesIO()
            can = canvas.Canvas(packet, pagesize=A4)
            can.saveState()
            can.setFont(active_font, 50)
            can.setFillColorRGB(0.8, 0.8, 0.8, alpha=0.15) # 워터마크 농도 조절
            can.translate(300, 450); can.rotate(45)
            can.drawCentredString(0, 0, watermark_text)
            can.restoreState()
            
            can.setFont(active_font, 10)
            can.drawRightString(550, 30, f"Page {i+1} / {len(reader.pages)}")
            can.save()

            packet.seek(0)
            overlay = PdfReader(packet)
            page.merge_page(overlay.pages[0])
            writer.add_page(page)

        with open(self.output_path, "wb") as f:
            writer.write(f)

    def optimize_pdf(self):
        try:
            with pikepdf.open(self.output_path, allow_overwriting_input=True) as pdf:
                pdf.save(self.output_path, linearize=True)
        except: pass

    def process_all(self):
        try:
            self.convert_to_pdf()
            self.add_overlays_and_bookmarks()
            self.optimize_pdf()
        finally:
            if os.path.exists(self.base_pdf): os.remove(self.base_pdf)
