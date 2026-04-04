import os
import uuid
import subprocess
import shutil
from io import BytesIO
import pikepdf
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader

from converter import run_libreoffice, SUPPORTED_IMAGE_EXTS


class PDFProcessor:
    def __init__(self, temp_dir):
        self.temp_dir = temp_dir

    def _convert_to_pdf_fragment(self, input_path):
        ext = input_path.split('.')[-1].lower()
        tmp_pdf = os.path.join(self.temp_dir, f"frag_{uuid.uuid4()}.pdf")

        # 🖼 이미지 → PDF
        if ext in SUPPORTED_IMAGE_EXTS:
            from PIL import Image
            with Image.open(input_path) as img:
                img.convert("RGB").save(tmp_pdf, "PDF")
            return tmp_pdf

        # 📄 LibreOffice 변환
        profile_dir = os.path.join(self.temp_dir, f"env_{uuid.uuid4().hex[:6]}")
        os.makedirs(profile_dir, exist_ok=True)

        try:
            env = os.environ.copy()
            env.update({"HOME": profile_dir, "LANG": "ko_KR.UTF-8"})

            run_libreoffice(input_path, profile_dir, env)

            gen_pdf = os.path.join(
                profile_dir,
                f"{os.path.basename(input_path).rsplit('.', 1)[0]}.pdf"
            )

            if os.path.exists(gen_pdf):
                shutil.move(gen_pdf, tmp_pdf)
                return tmp_pdf

            return None

        finally:
            shutil.rmtree(profile_dir, ignore_errors=True)

    def process_merge(
        self,
        input_paths,
        output_path,
        wm_type,
        wm_text,
        wm_image_path,
        wm_position,
        wm_size,
        wm_opacity,
        wm_rotation,
        user_pw,
        use_page_number
    ):
        fragments = [self._convert_to_pdf_fragment(p) for p in input_paths if p]
        fragments = [f for f in fragments if f]

        if not fragments:
            raise ValueError("변환된 PDF가 없습니다.")

        merged_raw = os.path.join(self.temp_dir, f"raw_{uuid.uuid4()}.pdf")

        # 🧩 Ghostscript 병합
        try:
            subprocess.run([
                "gs",
                "-sDEVICE=pdfwrite",
                "-dCompatibilityLevel=1.4",
                "-dNOPAUSE",
                "-dQUIET",
                "-dBATCH",
                f"-sOutputFile={merged_raw}"
            ] + fragments, check=True)
        except Exception as e:
            raise RuntimeError("Ghostscript 실행 실패 (설치 확인 필요)") from e

        with pikepdf.open(merged_raw) as pdf:
            logo = None
            if wm_type == "image" and wm_image_path:
                with open(wm_image_path, 'rb') as f:
                    logo = ImageReader(BytesIO(f.read()))

            for i, page in enumerate(pdf.pages):
                # 투명도 그룹 제거 (깨짐 방지)
                if "/Group" in page:
                    del page["/Group"]

                wm_packet = BytesIO()

                # ✅ 페이지 크기 맞춤 (중요!)
                page_width = float(page.MediaBox[2])
                page_height = float(page.MediaBox[3])

                can = canvas.Canvas(wm_packet, pagesize=(page_width, page_height))
                width, height = page_width, page_height

                pos_map = {
                    "center": (width/2, height/2),
                    "top-left": (width*0.2, height*0.85),
                    "top-right": (width*0.8, height*0.85),
                    "bottom-left": (width*0.2, height*0.15),
                    "bottom-right": (width*0.8, height*0.15)
                }
                x, y = pos_map.get(wm_position, (width/2, height/2))

                # 🎨 워터마크
                if wm_type == "image" and logo:
                    s = wm_size * mm
                    can.saveState()
                    can.translate(x, y)
                    can.rotate(wm_rotation)
                    can.setFillAlpha(max(0.1, min(wm_opacity, 1.0)))
                    can.drawImage(logo, -s/2, -s/2, width=s, height=s, mask='auto')
                    can.restoreState()

                elif wm_type == "text" and wm_text:
                    can.saveState()
                    can.setFont("Helvetica-Bold", wm_size)
                    can.setFillAlpha(max(0.1, min(wm_opacity, 1.0)))
                    can.translate(x, y)
                    can.rotate(wm_rotation)
                    can.drawCentredString(0, 0, wm_text)
                    can.restoreState()

                # 🔢 페이지 번호
                if use_page_number:
                    can.setFont("Helvetica", 10)
                    can.setFillAlpha(0.5)
                    can.drawCentredString(
                        width/2,
                        10*mm,
                        f"- Page {i+1} / {len(pdf.pages)} -"
                    )

                can.showPage()
                can.save()

                wm_packet.seek(0)
                with pikepdf.open(wm_packet) as wm_pdf:
                    page.add_overlay(wm_pdf.pages[0])

                wm_packet.close()

            # 🔐 저장 + 암호화
            save_args = {"static_id": True}
            if user_pw:
                save_args["encryption"] = pikepdf.Encryption(
                    user=user_pw,
                    owner=str(uuid.uuid4()),
                    R=4
                )

            pdf.save(output_path, **save_args)

        # 🧹 cleanup
        for f in fragments:
            if os.path.exists(f):
                os.remove(f)

        if os.path.exists(merged_raw):
            os.remove(merged_raw)
