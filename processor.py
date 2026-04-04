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

from converter import run_libreoffice, SUPPORTED_IMAGE_EXTS

logger = logging.getLogger("SixSense-Processor")


class PDFProcessor:
    def __init__(self, temp_dir):
        self.temp_dir = temp_dir

    def _convert_to_pdf_fragment(self, input_path):
        ext = input_path.split('.')[-1].lower()
        tmp_pdf = os.path.join(self.temp_dir, f"frag_{uuid.uuid4()}.pdf")

        # 🖼 이미지 → PDF
        if ext in SUPPORTED_IMAGE_EXTS:
            with PILImage.open(input_path) as img:
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

    def _prepare_wm_image_bytes(self, wm_image_path: str) -> bytes:
        """PIL로 이미지를 열어 RGB/RGBA 정규화 후 PNG bytes 반환."""
        logger.info(f"[WM] 이미지 전처리 시작: {wm_image_path}")
        logger.info(f"[WM] 파일 존재 여부: {os.path.exists(wm_image_path)}")
        logger.info(f"[WM] 파일 크기: {os.path.getsize(wm_image_path)} bytes")

        with PILImage.open(wm_image_path) as img:
            logger.info(f"[WM] PIL 이미지 열기 성공 - mode={img.mode}, size={img.size}, format={img.format}")
            original_mode = img.mode
            if img.mode not in ("RGBA", "RGB"):
                img = img.convert("RGB")
                logger.info(f"[WM] 색상 모드 변환: {original_mode} → RGB")
            buf = BytesIO()
            img.save(buf, format="PNG")
            buf.seek(0)
            result = buf.read()
            logger.info(f"[WM] PNG bytes 변환 완료 - {len(result)} bytes")
            return result

    def _is_rgba_png(self, image_bytes: bytes) -> bool:
        """PNG IHDR 청크에서 컬러 타입 6(RGBA) 여부 확인."""
        try:
            is_rgba = image_bytes[25] == 6
            logger.info(f"[WM] RGBA 여부: {is_rgba} (byte[25]={image_bytes[25]})")
            return is_rgba
        except IndexError:
            logger.warning("[WM] RGBA 확인 실패 - IndexError, False 반환")
            return False

    def _draw_watermark_layer(
        self,
        page_width: float,
        page_height: float,
        wm_type: str,
        wm_text: str,
        wm_image_bytes: bytes,
        wm_position: str,
        wm_size: float,
        wm_opacity: float,
        wm_rotation: float,
        page_num: int,
        total_pages: int,
        use_page_number: bool,
    ) -> BytesIO:
        """페이지 1장짜리 워터마크 PDF를 BytesIO로 반환."""
        logger.info(f"[WM] 페이지 {page_num}/{total_pages} 워터마크 레이어 생성 시작")
        logger.info(f"[WM]   wm_type={wm_type}, wm_size={wm_size}, wm_opacity={wm_opacity}, wm_rotation={wm_rotation}")
        logger.info(f"[WM]   page_width={page_width}, page_height={page_height}, wm_position={wm_position}")

        packet = BytesIO()
        can = canvas.Canvas(packet, pagesize=(page_width, page_height))

        pos_map = {
            "center":       (page_width / 2,       page_height / 2),
            "top-left":     (page_width * 0.2,     page_height * 0.85),
            "top-right":    (page_width * 0.8,     page_height * 0.85),
            "bottom-left":  (page_width * 0.2,     page_height * 0.15),
            "bottom-right": (page_width * 0.8,     page_height * 0.15),
        }
        x, y = pos_map.get(wm_position, (page_width / 2, page_height / 2))
        opacity = max(0.1, min(wm_opacity, 1.0))
        logger.info(f"[WM]   위치 x={x:.1f}, y={y:.1f}, opacity={opacity}")

        # 🎨 이미지 워터마크
        if wm_type == "image" and wm_image_bytes:
            logger.info(f"[WM]   이미지 워터마크 진입 - bytes 길이={len(wm_image_bytes)}")
            try:
                logo = ImageReader(BytesIO(wm_image_bytes))
                s = wm_size * mm
                is_rgba = self._is_rgba_png(wm_image_bytes)
                mask = 'auto' if is_rgba else None
                logger.info(f"[WM]   ImageReader 생성 완료 - s={s:.1f}mm, mask={mask}")

                can.saveState()
                can.translate(x, y)
                can.rotate(wm_rotation)
                can.setFillAlpha(opacity)
                can.drawImage(logo, -s / 2, -s / 2, width=s, height=s, mask=mask)
                can.restoreState()
                logger.info(f"[WM]   drawImage 완료")
            except Exception as e:
                logger.error(f"[WM]   ❌ 이미지 워터마크 그리기 실패: {e}", exc_info=True)
        elif wm_type == "image" and not wm_image_bytes:
            logger.error("[WM]   ❌ wm_type=image 인데 wm_image_bytes 가 None/비어있음!")

        # 🔤 텍스트 워터마크
        elif wm_type == "text" and wm_text:
            logger.info(f"[WM]   텍스트 워터마크 진입 - text='{wm_text}'")
            can.saveState()
            can.setFont("Helvetica-Bold", wm_size)
            can.setFillAlpha(opacity)
            can.translate(x, y)
            can.rotate(wm_rotation)
            can.drawCentredString(0, 0, wm_text)
            can.restoreState()

        # 🔢 페이지 번호
        if use_page_number:
            can.setFont("Helvetica", 10)
            can.setFillAlpha(0.5)
            can.drawCentredString(
                page_width / 2,
                10 * mm,
                f"- Page {page_num} / {total_pages} -"
            )

        can.showPage()
        can.save()
        packet.seek(0)

        packet_size = len(packet.getvalue())
        logger.info(f"[WM]   워터마크 PDF 패킷 생성 완료 - {packet_size} bytes")
        if packet_size < 500:
            logger.warning(f"[WM]   ⚠️ 워터마크 PDF 패킷이 너무 작음 ({packet_size} bytes) - 이미지 누락 의심")

        return packet

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
        logger.info("=" * 60)
        logger.info("[MERGE] process_merge 시작")
        logger.info(f"[MERGE] 입력 파일 수: {len(input_paths)}")
        logger.info(f"[MERGE] wm_type={wm_type}, wm_image_path={wm_image_path}")
        logger.info(f"[MERGE] wm_text={wm_text}, wm_position={wm_position}")
        logger.info(f"[MERGE] wm_size={wm_size}, wm_opacity={wm_opacity}, wm_rotation={wm_rotation}")
        logger.info(f"[MERGE] use_page_number={use_page_number}, pdf_pw={'설정됨' if user_pw else '없음'}")

        fragments = [self._convert_to_pdf_fragment(p) for p in input_paths if p]
        fragments = [f for f in fragments if f]
        logger.info(f"[MERGE] 변환된 fragment 수: {len(fragments)}")

        if not fragments:
            raise ValueError("변환된 PDF가 없습니다.")

        merged_raw = os.path.join(self.temp_dir, f"raw_{uuid.uuid4()}.pdf")

        # 🧩 Ghostscript 병합
        logger.info(f"[MERGE] Ghostscript 병합 시작 → {merged_raw}")
        try:
            result = subprocess.run([
                "gs",
                "-sDEVICE=pdfwrite",
                "-dCompatibilityLevel=1.4",
                "-dNOPAUSE",
                "-dQUIET",
                "-dBATCH",
                f"-sOutputFile={merged_raw}"
            ] + fragments, check=True, capture_output=True, text=True)
            logger.info(f"[MERGE] Ghostscript 완료 - 병합 파일 크기: {os.path.getsize(merged_raw)} bytes")
            if result.stderr:
                logger.warning(f"[MERGE] Ghostscript STDERR: {result.stderr}")
        except subprocess.CalledProcessError as e:
            logger.error(f"[MERGE] ❌ Ghostscript 실패: {e.stderr}")
            raise RuntimeError("Ghostscript 실행 실패 (설치 확인 필요)") from e

        # ✅ 워터마크 이미지 전처리
        wm_image_bytes = None
        if wm_type == "image":
            if wm_image_path and os.path.exists(wm_image_path):
                logger.info(f"[MERGE] 이미지 워터마크 전처리 시작")
                try:
                    wm_image_bytes = self._prepare_wm_image_bytes(wm_image_path)
                    logger.info(f"[MERGE] 이미지 전처리 성공 - {len(wm_image_bytes)} bytes")
                except Exception as e:
                    logger.error(f"[MERGE] ❌ 이미지 전처리 실패: {e}", exc_info=True)
            else:
                logger.error(f"[MERGE] ❌ wm_type=image 인데 wm_image_path 문제 - path={wm_image_path}, exists={os.path.exists(wm_image_path) if wm_image_path else 'N/A'}")

        with pikepdf.open(merged_raw) as pdf:
            total = len(pdf.pages)
            logger.info(f"[MERGE] 병합 PDF 열기 성공 - 총 {total} 페이지")

            for i, page in enumerate(pdf.pages):
                logger.info(f"[MERGE] --- 페이지 {i+1}/{total} 처리 중 ---")

                if "/Group" in page:
                    logger.info(f"[MERGE]   /Group 키 제거 (투명도 깨짐 방지)")
                    del page["/Group"]

                page_width  = float(page.MediaBox[2])
                page_height = float(page.MediaBox[3])
                logger.info(f"[MERGE]   MediaBox: width={page_width}, height={page_height}")

                try:
                    wm_packet = self._draw_watermark_layer(
                        page_width, page_height,
                        wm_type, wm_text, wm_image_bytes,
                        wm_position, wm_size, wm_opacity, wm_rotation,
                        i + 1, total, use_page_number
                    )

                    with pikepdf.open(wm_packet) as wm_pdf:
                        wm_page_count = len(wm_pdf.pages)
                        logger.info(f"[MERGE]   워터마크 PDF 열기 성공 - {wm_page_count} 페이지")
                        page.add_overlay(wm_pdf.pages[0])
                        logger.info(f"[MERGE]   add_overlay 완료")

                    wm_packet.close()

                except Exception as e:
                    logger.error(f"[MERGE]   ❌ 페이지 {i+1} 워터마크 적용 실패: {e}", exc_info=True)
                    raise

            # 🔐 저장 + 암호화
            save_args = {"static_id": True}
            if user_pw:
                save_args["encryption"] = pikepdf.Encryption(
                    user=user_pw,
                    owner=str(uuid.uuid4()),
                    R=4
                )

            logger.info(f"[MERGE] PDF 저장 시작 → {output_path}")
            pdf.save(output_path, **save_args)
            logger.info(f"[MERGE] PDF 저장 완료 - 크기: {os.path.getsize(output_path)} bytes")

        # 🧹 cleanup
        for f in fragments:
            if os.path.exists(f):
                os.remove(f)

        if os.path.exists(merged_raw):
            os.remove(merged_raw)

        logger.info("[MERGE] process_merge 완료")
        logger.info("=" * 60)
