import os
import subprocess
import logging
import time
import shutil

logger = logging.getLogger("SixSense-Converter")

# 지원 확장자 (processor.py와 공유)
SUPPORTED_IMAGE_EXTS = {"png", "jpg", "jpeg", "bmp"}
SUPPORTED_DOC_EXTS   = {"docx", "xlsx", "pptx", "txt", "hwp"}
SUPPORTED_EXTS       = SUPPORTED_IMAGE_EXTS | SUPPORTED_DOC_EXTS


def run_libreoffice(input_file: str, outdir: str, env: dict) -> None:
    """
    LibreOffice로 문서를 PDF로 변환합니다.

    - 독립 UserInstallation 경로로 설정 충돌 방지
    - writer_pdf_Export 필터로 표 레이아웃 보장
    - xvfb-run 가상 디스플레이로 그래픽 객체 인식률 향상
    """
    ts = str(int(time.time() * 1000))
    user_profile = os.path.join(env["HOME"], f"profile_{ts}")

    cmd = [
        "xvfb-run", "-a",
        "-s", "-screen 0 1920x1080x24 -ac +extension GLX +render -noreset",
        "libreoffice",
        f"-env:UserInstallation=file://{user_profile}",
        "--headless", "--invisible",
        "--nodefault", "--nofirststartwizard",
        "--nolockcheck", "--nologo", "--norestore",
        "--convert-to", "pdf:writer_pdf_Export",
        "--outdir", outdir,
        input_file,
    ]

    try:
        result = subprocess.run(
            cmd,
            env=env,
            capture_output=True,
            text=True,
            timeout=180,
        )

        if result.returncode != 0:
            logger.error("=== LibreOffice 변환 엔진 오류 ===")
            logger.error(f"STDOUT: {result.stdout}")
            logger.error(f"STDERR: {result.stderr}")
            raise RuntimeError(
                f"LibreOffice 실행 실패 (Exit Code: {result.returncode})"
            )

    finally:
        if os.path.exists(user_profile):
            shutil.rmtree(user_profile, ignore_errors=True)
