import os
import uuid
import shutil
import logging
import time  # 성능 측정을 위해 추가
from typing import Optional, List

import boto3
from fastapi import FastAPI, File, UploadFile, Form, HTTPException, BackgroundTasks, Request, status
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

#  Prometheus 모니터링을 위한 임포트
from prometheus_fastapi_instrumentator import Instrumentator
from prometheus_client import Histogram, Counter, Gauge

from processor import PDFProcessor
from templates import HTML_CONTENT

# -------------------------------
#  기본 설정 및 로깅
# -------------------------------
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("SixSense-Converter")

S3_BUCKET = os.getenv("S3_BUCKET_NAME", "sixsense-pdf-storage")
s3_client = boto3.client("s3", region_name="ap-northeast-2")

app = FastAPI(title="SixSense Doc-Converter", version="1.0.0")

# -------------------------------
#  커스텀 Prometheus 메트릭 정의
# -------------------------------
# 1. PDF 변환 소요 시간 측정 (Histogram)
PDF_PROCESSING_TIME = Histogram(
    "pdf_conversion_duration_seconds", 
    "Time spent converting documents to PDF",
    buckets=[1.0, 2.0, 5.0, 10.0, 30.0, 60.0, float("inf")]
)

# 2. S3 업로드 소요 시간 측정 (Histogram)
S3_UPLOAD_TIME = Histogram(
    "s3_upload_duration_seconds", 
    "Time spent uploading final PDF to S3",
    buckets=[0.5, 1.0, 2.0, 5.0, 10.0, float("inf")]
)

# 3. 변환 성공/실패 카운터 (Counter)
CONVERSION_COUNT = Counter(
    "pdf_conversion_total", 
    "Total count of PDF conversions", 
    ["status"] # success / fail 라벨링
)

# 4. 현재 진행 중인 PDF 변환 작업 수 (Gauge)
ACTIVE_CONVERSIONS = Gauge(
    "pdf_active_conversions_count",
    "Number of PDF conversions currently in progress"
)

# Prometheus 자동 계측 설정
Instrumentator().instrument(app).expose(app, endpoint="/metrics")

# -------------------------------
#  보안 및 인프라 설정
# -------------------------------
app.mount("/static", StaticFiles(directory="static"), name="static")

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

TEMP_DIR = os.path.join(os.path.dirname(__file__), "temp_storage")
os.makedirs(TEMP_DIR, exist_ok=True)


# -------------------------------
#  Health & Readiness Checks (K8s용)
# -------------------------------
@app.get("/health", status_code=status.HTTP_200_OK)
async def health_check():
    return {"status": "ok", "service": "SixSense-Doc-Converter"}

@app.get("/ready", status_code=status.HTTP_200_OK)
async def readiness_check():
    return {"status": "ready"}


# -------------------------------
#  파일 정리 함수
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
#  메인 페이지
# -------------------------------
@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return HTML_CONTENT


# -------------------------------
#  단일 변환 → 내부적으로 병합 함수 사용
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
#  병합 + 변환 (실시간 모니터링 포함)
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
        #  [Gauge] 실시간 변환 작업 수 증가
        ACTIVE_CONVERSIONS.inc()
        
        #  파일 저장
        for file in files:
            ext = os.path.splitext(file.filename)[1].lower().replace('.', '')
            path = os.path.join(TEMP_DIR, f"{uuid.uuid4()}.{ext}")
            with open(path, "wb") as f:
                while chunk := await file.read(1024 * 1024):
                    f.write(chunk)
            input_paths.append(path)

        #  워터마크 이미지 저장
        if wm_type == "image" and wm_image is not None:
            wm_image_data = await wm_image.read()
            if len(wm_image_data) > 0:
                wm_ext = os.path.splitext(wm_image.filename or "")[1].lower().lstrip('.') or "png"
                wm_image_path = os.path.join(TEMP_DIR, f"wm_{merge_id}.{wm_ext}")
                with open(wm_image_path, "wb") as f:
                    f.write(wm_image_data)

        #  [성능 측정] PDF 처리
        start_proc = time.perf_counter()
        proc = PDFProcessor(TEMP_DIR)
        proc.process_merge(
            input_paths, final_output_path, wm_type, wm_text,
            wm_image_path, wm_position, wm_size, wm_opacity,
            -wm_rotation, pdf_pw, use_pg_num
        )
        PDF_PROCESSING_TIME.observe(time.perf_counter() - start_proc)

        #  [성능 측정] S3 업로드
        s3_key = f"output/{merge_id}.pdf"
        start_s3 = time.perf_counter()
        s3_client.upload_file(final_output_path, S3_BUCKET, s3_key)
        S3_UPLOAD_TIME.observe(time.perf_counter() - start_s3)

        url = s3_client.generate_presigned_url(
            "get_object",
            Params={"Bucket": S3_BUCKET, "Key": s3_key},
            ExpiresIn=300
        )

        # 성공 카운트 증가
        CONVERSION_COUNT.labels(status="success").inc()

        #  백그라운드 정리
        for p in input_paths: background_tasks.add_task(cleanup, p)
        background_tasks.add_task(cleanup, final_output_path)
        if wm_image_path: background_tasks.add_task(cleanup, wm_image_path)

        return JSONResponse({"download_url": url})

    except Exception as e:
        # 실패 카운트 증가
        CONVERSION_COUNT.labels(status="fail").inc()
        logger.error(f"Error during conversion: {e}", exc_info=True)
        
        for p in input_paths: cleanup(p)
        if wm_image_path: cleanup(wm_image_path)
        if os.path.exists(final_output_path): cleanup(final_output_path)
        
        raise HTTPException(status_code=500, detail="변환 실패")

    finally:
        #  [Gauge] 성공/실패 여부와 상관없이 작업 종료 시 카운트 감소
        ACTIVE_CONVERSIONS.dec()
