import os
import uuid
import shutil
import logging
import boto3
import subprocess  # 압축을 위한 subprocess
from typing import Optional, List
from botocore.config import Config

from fastapi import FastAPI, File, UploadFile, Form, HTTPException, BackgroundTasks, Request
from fastapi.responses import HTMLResponse, JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# 📊 모니터링을 위한 라이브러리 추가
from prometheus_fastapi_instrumentator import Instrumentator
from prometheus_client import Counter, Histogram

from processor import PDFProcessor
from templates import HTML_CONTENT

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("SixSense-Converter")

S3_BUCKET = os.getenv("S3_BUCKET_NAME", "sixsense-pdf-storage")
s3_client = boto3.client('s3', region_name="ap-northeast-2", config=Config(signature_version='s3v4'))

# --- FastAPI 앱 초기화 ---
app = FastAPI()

# 🚀 [수정 포인트] Instrumentator를 startup 이벤트 밖으로 이동
# 서버 기동 전 미들웨어를 미리 등록해야 RuntimeError를 피할 수 있습니다. 🎖️
Instrumentator().instrument(app).expose(app)

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# --- 커스텀 메트릭 정의 ---
CONVERSION_STATS = Counter(
    "sixsense_conversion_total",
    "Total count of PDF conversions",
    ["mode", "status"]
)
S3_UPLOAD_LATENCY = Histogram(
    "sixsense_s3_upload_duration_seconds",
    "Duration of S3 upload in seconds"
)

TEMP_DIR = os.path.join(os.path.dirname(__file__), "temp_storage")
os.makedirs(TEMP_DIR, exist_ok=True)

def compress_pdf_high_quality(input_path, output_path):
    if not os.path.exists(input_path):
        return False
    gs_command = [
        "gs", "-sDEVICE=pdfwrite", "-dCompatibilityLevel=1.4",
        "-dPDFSETTINGS=/printer", "-dNOPAUSE", "-dQUIET", "-dBATCH",
        "-dDetectDuplicateImages=true", "-dDownsampleColorImages=true",
        "-dColorImageResolution=300", f"-sOutputFile={output_path}", input_path
    ]
    try:
        subprocess.run(gs_command, check=True)
        return True
    except Exception as e:
        logger.error(f"❌ 압축 실패: {e}")
        return False

def cleanup(path):
    if path and os.path.exists(path):
        if os.path.isfile(path): os.remove(path)
        else: shutil.rmtree(path)

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return HTML_CONTENT

# 1. 단일 파일 변환
@app.post("/convert-single/")
@limiter.limit("10/minute")
async def convert_single(
    request: Request,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    wm_type: str = Form("none"),
    wm_text: Optional[str] = Form(None),
    wm_image: Optional[UploadFile] = File(None)
):
    ext = file.filename.split(".")[-1].lower()
    file_id = str(uuid.uuid4())
    input_path = os.path.join(TEMP_DIR, f"{file_id}.{ext}")
    temp_output_path = os.path.join(TEMP_DIR, f"{file_id}_raw.pdf")
    final_output_path = os.path.join(TEMP_DIR, f"{file_id}.pdf")
    wm_image_path = None

    try:
        with open(input_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        if wm_type == "image" and wm_image and wm_image.filename:
            wm_ext = wm_image.filename.split(".")[-1].lower()
            wm_image_path = os.path.join(TEMP_DIR, f"wm_{file_id}.{wm_ext}")
            with open(wm_image_path, "wb") as wm_buffer:
                shutil.copyfileobj(wm_image.file, wm_buffer)

        proc = PDFProcessor(TEMP_DIR)
        actual_wm_type = wm_type if wm_type != "none" else None
        proc.process_merge([input_path], temp_output_path, actual_wm_type, wm_text, wm_image_path)

        if not compress_pdf_high_quality(temp_output_path, final_output_path):
            shutil.copy(temp_output_path, final_output_path)

        # S3 업로드 시간 측정 및 카운팅
        with S3_UPLOAD_LATENCY.time():
            s3_client.upload_file(final_output_path, S3_BUCKET, s3_key := f"single/{file_id}.pdf")

        CONVERSION_STATS.labels(mode="single", status="success").inc()

        url = s3_client.generate_presigned_url('get_object', Params={'Bucket': S3_BUCKET, 'Key': s3_key}, ExpiresIn=300)

        background_tasks.add_task(cleanup, input_path)
        background_tasks.add_task(cleanup, temp_output_path)
        background_tasks.add_task(cleanup, final_output_path)
        if wm_image_path: background_tasks.add_task(cleanup, wm_image_path)

        return JSONResponse({"download_url": url})
    except Exception as e:
        CONVERSION_STATS.labels(mode="single", status="fail").inc()
        logger.error(f"Error during single conversion: {e}")
        cleanup(input_path); cleanup(temp_output_path); cleanup(final_output_path)
        if wm_image_path: cleanup(wm_image_path)
        raise HTTPException(status_code=500, detail=str(e))

# 2. 다중 파일 병합
@app.post("/convert-merge/")
@limiter.limit("5/minute")
async def convert_merge(
    request: Request,
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = File(...),
    wm_type: str = Form("none"),
    wm_text: Optional[str] = Form(None),
    wm_image: Optional[UploadFile] = File(None)
):
    if len(files) > 10:
        raise HTTPException(status_code=400, detail="최대 10개의 파일까지만 병합 가능합니다.")

    merge_id = str(uuid.uuid4())
    input_paths = []
    temp_output_path = os.path.join(TEMP_DIR, f"{merge_id}_raw.pdf")
    final_output_path = os.path.join(TEMP_DIR, f"{merge_id}_merged.pdf")
    wm_image_path = None

    try:
        for file in files:
            ext = file.filename.split(".")[-1].lower()
            path = os.path.join(TEMP_DIR, f"{uuid.uuid4()}.{ext}")
            with open(path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            input_paths.append(path)

        if wm_type == "image" and wm_image and wm_image.filename:
            wm_ext = wm_image.filename.split(".")[-1].lower()
            wm_image_path = os.path.join(TEMP_DIR, f"wm_m_{merge_id}.{wm_ext}")
            with open(wm_image_path, "wb") as wm_buffer:
                shutil.copyfileobj(wm_image.file, wm_buffer)

        proc = PDFProcessor(TEMP_DIR)
        actual_wm_type = wm_type if wm_type != "none" else None
        proc.process_merge(input_paths, temp_output_path, actual_wm_type, wm_text, wm_image_path)

        if not compress_pdf_high_quality(temp_output_path, final_output_path):
            shutil.copy(temp_output_path, final_output_path)

        # S3 업로드 시간 측정 및 카운팅
        with S3_UPLOAD_LATENCY.time():
            s3_client.upload_file(final_output_path, S3_BUCKET, s3_key := f"merged/{merge_id}.pdf")

        CONVERSION_STATS.labels(mode="merge", status="success").inc()

        url = s3_client.generate_presigned_url('get_object', Params={'Bucket': S3_BUCKET, 'Key': s3_key}, ExpiresIn=300)

        for p in input_paths: background_tasks.add_task(cleanup, p)
        background_tasks.add_task(cleanup, temp_output_path)
        background_tasks.add_task(cleanup, final_output_path)
        if wm_image_path: background_tasks.add_task(cleanup, wm_image_path)

        return JSONResponse({"download_url": url})
    except Exception as e:
        CONVERSION_STATS.labels(mode="merge", status="fail").inc()
        logger.error(f"Merge Error: {e}")
        for p in input_paths: cleanup(p)
        cleanup(temp_output_path); cleanup(final_output_path)
        if wm_image_path: cleanup(wm_image_path)
        raise HTTPException(status_code=500, detail=str(e))
