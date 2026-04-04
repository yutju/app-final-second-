import os
import uuid
import shutil
import logging
from typing import Optional, List

import boto3
from fastapi import FastAPI, File, UploadFile, Form, HTTPException, BackgroundTasks, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from processor import PDFProcessor
from templates import HTML_CONTENT

# -------------------------------
# 🔧 기본 설정
# -------------------------------
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("SixSense-Converter")

S3_BUCKET = os.getenv("S3_BUCKET_NAME", "sixsense-pdf-storage")
s3_client = boto3.client("s3", region_name="ap-northeast-2")

app = FastAPI()

# Static 파일 서빙 (/static → /app/static 디렉토리)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Rate Limiter
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

TEMP_DIR = os.path.join(os.path.dirname(__file__), "temp_storage")
os.makedirs(TEMP_DIR, exist_ok=True)


# -------------------------------
# 🧹 파일 정리 함수
# -------------------------------
def cleanup(path):
    try:
        if path and os.path.exists(path):
            if os.path.isfile(path):
                os.remove(path)
            else:
                shutil.rmtree(path)
    except Exception as e:
        logger.warning(f"Cleanup failed: {path} - {e}")


# -------------------------------
# 🌐 메인 페이지
# -------------------------------
@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return HTML_CONTENT


# -------------------------------
# 📄 단일 변환 → 내부적으로 병합 함수 사용
# -------------------------------
@app.post("/convert-single/")
@limiter.limit("10/minute")
async def convert_single(
    request: Request,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    wm_type: str = Form("none"),
    wm_text: Optional[str] = Form(None),
    wm_image: Optional[UploadFile] = File(None),
    wm_position: str = Form("center"),
    wm_size: float = Form(60.0),
    wm_opacity: float = Form(0.3),
    wm_rotation: float = Form(45.0),
    pdf_pw: Optional[str] = Form(None),
    use_pg_num: bool = Form(False)
):
    return await convert_merge(
        request,
        background_tasks,
        [file],
        wm_type,
        wm_text,
        wm_image,
        wm_position,
        wm_size,
        wm_opacity,
        wm_rotation,
        pdf_pw,
        use_pg_num
    )


# -------------------------------
# 📑 병합 + 변환
# -------------------------------
@app.post("/convert-merge/")
@limiter.limit("5/minute")
async def convert_merge(
    request: Request,
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = File(...),
    wm_type: str = Form("none"),
    wm_text: Optional[str] = Form(None),
    wm_image: Optional[UploadFile] = File(None),
    wm_position: str = Form("center"),
    wm_size: float = Form(60.0),
    wm_opacity: float = Form(0.3),
    wm_rotation: float = Form(45.0),
    pdf_pw: Optional[str] = Form(None),
    use_pg_num: bool = Form(False)
):
    merge_id = str(uuid.uuid4())
    input_paths = []
    final_output_path = os.path.join(TEMP_DIR, f"{merge_id}_final.pdf")
    wm_image_path = None

    try:
        # -------------------------------
        # 📂 파일 저장 (메모리 안전)
        # -------------------------------
        for file in files:
            ext = os.path.splitext(file.filename)[1].lower().replace('.', '')
            path = os.path.join(TEMP_DIR, f"{uuid.uuid4()}.{ext}")

            with open(path, "wb") as f:
                while chunk := await file.read(1024 * 1024):
                    f.write(chunk)

            input_paths.append(path)

        # -------------------------------
        # 🖼 워터마크 이미지 저장 (스트림 한 번에 읽기)
        # -------------------------------
        if wm_type == "image" and wm_image is not None:
            logger.info(f"[MAIN] 워터마크 이미지 수신 - filename={wm_image.filename}, content_type={wm_image.content_type}")
            try:
                wm_image_data = await wm_image.read()
                logger.info(f"[MAIN] 워터마크 이미지 read() 완료 - {len(wm_image_data)} bytes")
                if len(wm_image_data) > 0:
                    wm_ext = os.path.splitext(wm_image.filename or "")[1].lower().lstrip('.') or "png"
                    wm_image_path = os.path.join(TEMP_DIR, f"wm_{merge_id}.{wm_ext}")
                    with open(wm_image_path, "wb") as f:
                        f.write(wm_image_data)
                    logger.info(f"[MAIN] 워터마크 이미지 저장 완료 - {wm_image_path} ({os.path.getsize(wm_image_path)} bytes)")
                else:
                    logger.error("[MAIN] ❌ 워터마크 이미지 데이터가 비어있음 (0 bytes)")
            except Exception as e:
                logger.error(f"[MAIN] ❌ 워터마크 이미지 저장 실패: {e}", exc_info=True)
                wm_image_path = None
        else:
            logger.info(f"[MAIN] 워터마크 이미지 없음 - wm_type={wm_type}, wm_image={wm_image}")

        # -------------------------------
        # ⚙️ PDF 처리
        # -------------------------------
        proc = PDFProcessor(TEMP_DIR)
        proc.process_merge(
            input_paths,
            final_output_path,
            wm_type,
            wm_text,
            wm_image_path,
            wm_position,
            wm_size,
            wm_opacity,
            -wm_rotation,  # UI 방향 보정
            pdf_pw,
            use_pg_num
        )

        # -------------------------------
        # ☁️ S3 업로드
        # -------------------------------
        s3_key = f"output/{merge_id}.pdf"

        s3_client.upload_file(final_output_path, S3_BUCKET, s3_key)

        url = s3_client.generate_presigned_url(
            "get_object",
            Params={"Bucket": S3_BUCKET, "Key": s3_key},
            ExpiresIn=300
        )

        # -------------------------------
        # 🧹 백그라운드 정리
        # -------------------------------
        for p in input_paths:
            background_tasks.add_task(cleanup, p)

        background_tasks.add_task(cleanup, final_output_path)

        if wm_image_path:
            background_tasks.add_task(cleanup, wm_image_path)

        return JSONResponse({"download_url": url})

    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)

        for p in input_paths:
            cleanup(p)

        if wm_image_path:
            cleanup(wm_image_path)

        if os.path.exists(final_output_path):
            cleanup(final_output_path)

        raise HTTPException(status_code=500, detail="변환 실패")
