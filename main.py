import os
import uuid
import shutil
import logging
import boto3
import time
import subprocess
from typing import Optional, List
from botocore.config import Config

from fastapi import FastAPI, File, UploadFile, Form, HTTPException, BackgroundTasks, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles  #  정적 파일 처리를 위해 추가
from starlette.responses import Response

#  모니터링 라이브러리
from prometheus_fastapi_instrumentator import Instrumentator
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST

# 사용자 정의 모듈
from processor import PDFProcessor
from templates import HTML_CONTENT

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("SixSense-Converter")

# 환경 변수 및 S3 설정
S3_BUCKET = os.getenv("S3_BUCKET_NAME", "sixsense-pdf-storage")
# Signature V4 설정을 통해 보안이 강화된 S3 통신을 지원합니다.
s3_client = boto3.client(
    's3', 
    region_name="ap-northeast-2", 
    config=Config(signature_version='s3v4')
)

# --- FastAPI 앱 초기화 ---
app = FastAPI(title="SixSense Doc Converter")

#  [인프라 포인트] 정적 파일 경로 등록
# 서버의 ~/app/static 폴더를 웹의 /static 경로로 연결하여 로고 등을 서빙합니다.
if not os.path.exists("static"):
    os.makedirs("static", exist_ok=True)

app.mount("/static", StaticFiles(directory="static"), name="static")

#  Prometheus 모니터링 계측기 설정 (Middleware 등록)
Instrumentator().instrument(app).expose(app)

# Rate Limiter 설정 (무분별한 요청 방지)
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

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

# --- 유틸리티 함수 ---
def compress_pdf_high_quality(input_path, output_path):
    """Ghostscript를 사용하여 PDF 용량을 최적화합니다."""
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
        logger.error(f"❌ PDF 압축 실패: {e}")
        return False

def cleanup(path):
    """작업이 끝난 임시 파일을 안전하게 삭제합니다."""
    if path and os.path.exists(path):
        if os.path.isfile(path): os.remove(path)
        else: shutil.rmtree(path)

# --- API 엔드포인트 ---

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    """메인 페이지 렌더링"""
    return HTML_CONTENT

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
    """단일 파일 PDF 변환 및 S3 업로드"""
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

        # S3 업로드 및 성능 측정
        with S3_UPLOAD_LATENCY.time():
            s3_key = f"single/{file_id}.pdf"
            s3_client.upload_file(final_output_path, S3_BUCKET, s3_key)

        CONVERSION_STATS.labels(mode="single", status="success").inc()

        # 5분 유효 보안 URL 생성
        url = s3_client.generate_presigned_url(
            'get_object', 
            Params={'Bucket': S3_BUCKET, 'Key': s3_key}, 
            ExpiresIn=300
        )

        # 백그라운드 파일 정리
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
    """여러 파일 병합 후 PDF 변환"""
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

        with S3_UPLOAD_LATENCY.time():
            s3_key = f"merged/{merge_id}.pdf"
            s3_client.upload_file(final_output_path, S3_BUCKET, s3_key)

        CONVERSION_STATS.labels(mode="merge", status="success").inc()

        url = s3_client.generate_presigned_url(
            'get_object', 
            Params={'Bucket': S3_BUCKET, 'Key': s3_key}, 
            ExpiresIn=300
        )

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
