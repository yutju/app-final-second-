# main.py
import os
import uuid
import shutil
import logging
import time
import boto3
from typing import List
from botocore.config import Config

try:
    from pypdf import PdfWriter as PdfMerger
except ImportError:
    from pypdf import PdfMerger

from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks, Request
from fastapi.responses import HTMLResponse, JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from processor import PDFProcessor
from templates import HTML_CONTENT

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("SixSense-Converter")

S3_BUCKET = os.getenv("S3_BUCKET_NAME", "sixsense-pdf-storage")
s3_client = boto3.client('s3', region_name="ap-northeast-2", config=Config(signature_version='s3v4'))

app = FastAPI()
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

TEMP_DIR = os.path.join(os.path.dirname(__file__), "temp_storage")
os.makedirs(TEMP_DIR, exist_ok=True)

def cleanup(path):
    if os.path.exists(path):
        if os.path.isfile(path): os.remove(path)
        else: shutil.rmtree(path)

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return HTML_CONTENT

@app.post("/convert-single/")
@limiter.limit("10/minute")
async def convert_single(request: Request, background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    ext = file.filename.split(".")[-1].lower()
    file_id = str(uuid.uuid4())
    input_path = os.path.join(TEMP_DIR, f"{file_id}.{ext}")
    output_path = os.path.join(TEMP_DIR, f"{file_id}.pdf")

    try:
        with open(input_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        proc = PDFProcessor(input_path, output_path, TEMP_DIR)
        proc.process_all()

        s3_key = f"single/{file_id}.pdf"
        s3_client.upload_file(output_path, S3_BUCKET, s3_key)
        
        url = s3_client.generate_presigned_url('get_object', Params={'Bucket': S3_BUCKET, 'Key': s3_key}, ExpiresIn=300)
        
        background_tasks.add_task(cleanup, input_path)
        background_tasks.add_task(cleanup, output_path)
        return JSONResponse({"download_url": url})
    except Exception as e:
        logger.error(f"Error during conversion: {e}")
        cleanup(input_path)
        cleanup(output_path)
        raise HTTPException(status_code=500, detail=str(e))
