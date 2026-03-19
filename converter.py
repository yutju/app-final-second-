# converter.py
import os
import subprocess
from PIL import Image

def process_conversion(input_path, output_path, ext, temp_dir):
    # 1. 이미지 파일 처리 (Pillow 사용)
    if ext in ["png", "jpg", "jpeg", "bmp"]:
        img = Image.open(input_path)
        if img.mode != "RGB":
            img = img.convert("RGB")
        img.save(output_path, "PDF")
        
    # 2. 문서 파일 처리 (LibreOffice soffice 엔진 사용)
    elif ext in ["docx", "doc", "hwp", "txt"]:
        # hwp와 docx의 성공률을 높이기 위해 필터를 명시적으로 지정합니다.
        # --headless: 화면 없이 실행
        # pdf:writer_pdf_Export: 워드프로세서 문서를 PDF로 내보내는 필터
        command = [
            "soffice", 
            "--headless", 
            "--convert-to", "pdf:writer_pdf_Export",
            "--outdir", temp_dir, 
            input_path
        ]
        
        # 엔진 실행 및 에러 체크
        subprocess.run(command, check=True)
        
    else:
        raise ValueError(f"지원하지 않는 형식입니다: {ext}")
