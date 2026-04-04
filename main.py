import os
import uuid
import shutil
import logging
import time
from enum import Enum
from typing import Optional, List

import boto3
from botocore.config import Config

from fastapi import FastAPI, File, UploadFile, Form, HTTPException, BackgroundTasks, Request, Response, status
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from prometheus_fastapi_instrumentator import Instrumentator
from prometheus_client import Counter, Histogram

from processor import PDFProcessor
from converter import SUPPORTED_EXTS
from templates import HTML_CONTENT

# [운영 포인트] 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("SixSense-Converter")

# 🕵️ [인프라 포인트] 환경변수를 통한 S3 버킷 설정
S3_BUCKET = os.getenv("S3_BUCKET_NAME", "sixsense-pdf-storage")

# IAM Role 기반 S3 클라이언트 (인스턴스 프로파일 + 자동 재시도)
s3_client = boto3.client(
    's3',
    region_name="ap-northeast-2",
    config=Config(
        retries={"max_attempts": 3, "mode": "standard"},
        connect_timeout=5,
        read_timeout=60,
    ),
)

# --- FastAPI 앱 초기화 ---
app = FastAPI(title="SixSense Doc Converter")

# 정적 파일 서빙 설정
if not os.path.exists("static"):
    os.makedirs("static", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

# [모니터링 포인트] Prometheus 계측기 활성화
Instrumentator().instrument(app).expose(app)

# Rate Limiter
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

# 임시 저장소 설정
TEMP_DIR = os.path.join(os.path.dirname(__file__), "temp_storage")
os.makedirs(TEMP_DIR, exist_ok=True)

# 업로드 제한
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB

# 워터마크 위치 허용값 Enum
class WatermarkPosition(str, Enum):
    center       = "center"
    top_left     = "top-left"
    top_right    = "top-right"
    bottom_left  = "bottom-left"
    bottom_right = "bottom-right"

def validate_upload(filename: str, size: int) -> str:
    """확장자 및 파일 크기 검증. 통과 시 ext 반환, 실패 시 HTTPException."""
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext not in SUPPORTED_EXTS:
        raise HTTPException(
            status_code=415,
            detail=f"지원하지 않는 파일 형식입니다: .{ext}  (지원: {', '.join(sorted(SUPPORTED_EXTS))})"
        )
    if size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"파일 크기 초과: {filename} ({size // (1024*1024)}MB). 최대 50MB까지 허용됩니다."
        )
    return ext

# --- 유틸리티 함수 ---
def compress_pdf_high_quality(input_path, output_path):
    """Ghostscript 엔진을 활용한 고성능 PDF 압축 최적화"""
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
    """서버 자원 관리를 위한 임시 파일 즉시 삭제"""
    if path and os.path.exists(path):
        if os.path.isfile(path): os.remove(path)
        else: shutil.rmtree(path)

# --- API 엔드포인트 ---

@app.get("/health", tags=["Health Check"])
async def health_check():
    """Liveness Probe: 컨테이너 생존 확인"""
    return {"status": "alive", "timestamp": time.time()}

@app.get("/ready", tags=["Health Check"])
async def readiness_check(response: Response):
    """Readiness Probe: 서비스 준비 상태 확인"""
    try:
        # 스토리지 쓰기 권한 및 환경변수 로드 확인
        if not os.access(TEMP_DIR, os.W_OK):
            raise Exception("Temporary storage is not writable")
        if not S3_BUCKET:
            raise Exception("S3_BUCKET_NAME environment variable is missing")
        return {"status": "ready", "bucket": S3_BUCKET}
    except Exception as e:
        logger.error(f"❌ Readiness Check Failed: {e}")
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {"status": "not ready", "reason": str(e)}

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return HTML_CONTENT

@app.post("/convert-single/")
@limiter.limit("10/minute")
async def convert_single(
    request: Request,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    wm_type: str = Form("none"),
    wm_text: Optional[str] = Form(None),
    wm_image: Optional[UploadFile] = File(None),
    wm_position: WatermarkPosition = Form(WatermarkPosition.center),
    wm_size: float = Form(60.0),             # 텍스트: pt / 이미지: mm
    wm_opacity: float = Form(0.3),           # 0.0 ~ 1.0
    wm_rotation: float = Form(45.0),         # 회전각 (도)
):
    content = await file.read()
    ext = validate_upload(file.filename, len(content))

    file_id = str(uuid.uuid4())
    input_path = os.path.join(TEMP_DIR, f"{file_id}.{ext}")
    temp_output_path = os.path.join(TEMP_DIR, f"{file_id}_raw.pdf")
    final_output_path = os.path.join(TEMP_DIR, f"{file_id}.pdf")
    wm_image_path = None

    try:
        with open(input_path, "wb") as buffer:
            buffer.write(content)

        if wm_type == "image" and wm_image and wm_image.filename:
            wm_ext = wm_image.filename.split(".")[-1].lower()
            wm_image_path = os.path.join(TEMP_DIR, f"wm_{file_id}.{wm_ext}")
            with open(wm_image_path, "wb") as wm_buffer:
                shutil.copyfileobj(wm_image.file, wm_buffer)

        proc = PDFProcessor(TEMP_DIR)
        actual_wm_type = wm_type if wm_type != "none" else None
        proc.process_merge(
            [input_path], temp_output_path,
            actual_wm_type, wm_text, wm_image_path,
            wm_position=wm_position,
            wm_size=wm_size,
            wm_opacity=wm_opacity,
            wm_rotation=wm_rotation,
        )

        if not compress_pdf_high_quality(temp_output_path, final_output_path):
            shutil.copy(temp_output_path, final_output_path)

        with S3_UPLOAD_LATENCY.time():
            s3_key = f"single/{file_id}.pdf"
            s3_client.upload_file(final_output_path, S3_BUCKET, s3_key)

        CONVERSION_STATS.labels(mode="single", status="success").inc()

        url = s3_client.generate_presigned_url(
            'get_object',
            Params={'Bucket': S3_BUCKET, 'Key': s3_key},
            ExpiresIn=300
        )

        background_tasks.add_task(cleanup, input_path)
        background_tasks.add_task(cleanup, temp_output_path)
        background_tasks.add_task(cleanup, final_output_path)
        if wm_image_path: background_tasks.add_task(cleanup, wm_image_path)

        return JSONResponse({"download_url": url})
    except Exception as e:
        CONVERSION_STATS.labels(mode="single", status="fail").inc()
        logger.error(f"[single] 변환 실패: {e}", exc_info=True)
        cleanup(input_path); cleanup(temp_output_path); cleanup(final_output_path)
        if wm_image_path: cleanup(wm_image_path)
        raise HTTPException(status_code=500, detail="파일 변환 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요.")

@app.post("/convert-merge/")
@limiter.limit("5/minute")
async def convert_merge(
    request: Request,
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = File(...),
    wm_type: str = Form("none"),
    wm_text: Optional[str] = Form(None),
    wm_image: Optional[UploadFile] = File(None),
    wm_position: WatermarkPosition = Form(WatermarkPosition.center),
    wm_size: float = Form(60.0),             # 텍스트: pt / 이미지: mm
    wm_opacity: float = Form(0.3),           # 0.0 ~ 1.0
    wm_rotation: float = Form(45.0),         # 회전각 (도)
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
            content = await file.read()
            ext = validate_upload(file.filename, len(content))
            path = os.path.join(TEMP_DIR, f"{uuid.uuid4()}.{ext}")
            with open(path, "wb") as buffer:
                buffer.write(content)
            input_paths.append(path)

        if wm_type == "image" and wm_image and wm_image.filename:
            wm_ext = wm_image.filename.split(".")[-1].lower()
            wm_image_path = os.path.join(TEMP_DIR, f"wm_m_{merge_id}.{wm_ext}")
            with open(wm_image_path, "wb") as wm_buffer:
                shutil.copyfileobj(wm_image.file, wm_buffer)

        proc = PDFProcessor(TEMP_DIR)
        actual_wm_type = wm_type if wm_type != "none" else None
        proc.process_merge(
            input_paths, temp_output_path,
            actual_wm_type, wm_text, wm_image_path,
            wm_position=wm_position,
            wm_size=wm_size,
            wm_opacity=wm_opacity,
            wm_rotation=wm_rotation,
        )

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
        logger.error(f"[merge] 변환 실패: {e}", exc_info=True)
        for p in input_paths: cleanup(p)
        cleanup(temp_output_path); cleanup(final_output_path)
        if wm_image_path: cleanup(wm_image_path)
        raise HTTPException(status_code=500, detail="파일 병합 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요.")
