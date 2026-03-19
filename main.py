# main.py (TypeError 수정 완료 버전)
import os
import uuid
import shutil
import logging
from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse, HTMLResponse

from templates import HTML_CONTENT
from converter import process_conversion

# --- [1. 로그 및 환경 설정] ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("app.log", encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("SixSense-Converter")

app = FastAPI(title="SixSense Doc-Converter")
TEMP_DIR = "temp_storage"
os.makedirs(TEMP_DIR, exist_ok=True)

# --- [2. 로컬 파일 정리 함수] ---
def cleanup_local_files(*filepaths: str):
    for path in filepaths:
        try:
            if os.path.exists(path):
                os.remove(path)
                logger.info(f"Cleanup: Local file removed at {path}")
        except Exception as e:
            logger.error(f"Cleanup Error for {path}: {str(e)}")

# 1. 루트 경로
@app.get("/", response_class=HTMLResponse)
async def read_root():
    logger.info("Root page accessed")
    return HTML_CONTENT

# 2. 헬스 체크
@app.get("/health")
async def health_check():
    return {"status": "healthy"}

# 3. 변환 경로 (수정됨)
@app.post("/convert-to-pdf/")
async def convert_any_to_pdf(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    # --- [수정 구간: 파일 용량 제한 체크] ---
    MAX_SIZE = 100 * 1024 * 1024
    
    # 비동기 seek 대신 표준 파일 객체(file.file)를 사용합니다.
    file.file.seek(0, os.SEEK_END)
    file_size = file.file.tell()
    file.file.seek(0)

    if file_size > MAX_SIZE:
        logger.warning(f"File size limit exceeded: {file.filename} ({file_size} bytes)")
        raise HTTPException(status_code=413, detail="파일이 너무 큽니다. 최대 100MB까지 가능합니다.")
    # --- [수정 완료] ---

    file_id = str(uuid.uuid4())
    ext = file.filename.split(".")[-1].lower()

    input_path = os.path.join(TEMP_DIR, f"{file_id}.{ext}")
    output_path = os.path.join(TEMP_DIR, f"{file_id}.pdf")

    logger.info(f"Starting conversion: {file.filename} -> {file_id}.pdf")

    with open(input_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    try:
        process_conversion(input_path, output_path, ext, TEMP_DIR)
        logger.info(f"Successfully converted: {file.filename}")

        background_tasks.add_task(cleanup_local_files, input_path, output_path)

        return FileResponse(
            output_path,
            media_type="application/pdf",
            filename=f"converted_{file.filename.rsplit('.', 1)[0]}.pdf"
        )

    except Exception as e:
        logger.error(f"Conversion failed for {file.filename}: {str(e)}")
        cleanup_local_files(input_path, output_path)
        raise HTTPException(status_code=500, detail=f"변환 실패: {str(e)}")
