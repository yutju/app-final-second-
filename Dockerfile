# 1단계: 베이스 이미지 선택
FROM python:3.9-slim

# 2단계: 환경변수 설정
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
# 한글 로케일 환경변수 설정 (HWP 변환 시 필수)
ENV LANG=ko_KR.UTF-8
ENV LC_ALL=ko_KR.UTF-8

# 3단계: 시스템 패키지 및 HWP 변환용 엔진 설치
# 최신 데비안(Trixie)에서 통합된 fonts-nanum-coding은 제외하고 설치합니다.
RUN apt-get update && apt-get install -y --no-install-recommends \
    libreoffice-writer \
    libreoffice-java-common \
    default-jre \
    fonts-nanum \
    fonts-nanum-extra \
    locales \
    && locale-gen ko_KR.UTF-8 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# 4단계: 작업 디렉토리 생성
WORKDIR /app

# 5단계: 파이썬 라이브러리 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 6단계: 소스 코드 복사
COPY . .

# 7단계: 임시 저장소 폴더 권한 설정
# 컨테이너 실행 시 권한 문제가 없도록 확실히 777 부여
RUN mkdir -p temp_storage && chmod 777 temp_storage

# 8단계: 컨테이너 실행 명령어
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
