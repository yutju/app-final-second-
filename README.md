# SixSense Doc Converter

문서 파일을 PDF로 변환하고, 워터마크 삽입 및 다중 파일 병합을 지원하는 FastAPI 기반 서비스입니다. 변환된 파일은 AWS S3에 업로드되며, 5분간 유효한 Pre-signed URL로 안전하게 배포됩니다.

---

## 주요 기능

- **단일 파일 변환** — `docx`, `txt`, `hwp`, `png`, `jpg`, `jpeg`, `bmp` → PDF
- **다중 파일 병합** — 최대 10개 파일을 하나의 PDF로 병합
- **워터마크 삽입** — 텍스트 또는 이미지 워터마크 지원
- **PDF 압축** — Ghostscript 기반 고품질 압축
- **S3 업로드 및 Pre-signed URL** — 변환 완료 후 5분 유효 다운로드 링크 발급
- **Rate Limiting** — slowapi 기반 API 호출 횟수 제한
- **Prometheus 메트릭** — 변환 횟수, S3 업로드 지연 등 실시간 모니터링

---

## 프로젝트 구조

```
.
├── main.py           # FastAPI 앱, 엔드포인트, S3 연동
├── processor.py      # PDF 변환, 병합, 워터마크 처리
├── converter.py      # LibreOffice 실행 및 단일 파일 변환
├── templates.py      # 프론트엔드 HTML 템플릿
├── components.py     # About / API 섹션 HTML 컴포넌트
├── requirements.txt  # Python 의존성
└── Dockerfile        # 컨테이너 빌드 설정
```

---

## 기술 스택

| 영역 | 사용 기술 |
|---|---|
| 웹 프레임워크 | FastAPI, Uvicorn |
| 문서 변환 엔진 | LibreOffice (xvfb-run), Pillow |
| PDF 처리 | pikepdf, pypdf, ReportLab |
| PDF 압축 | Ghostscript |
| 클라우드 스토리지 | AWS S3 (boto3, IAM Pre-signed URL) |
| 보안 / 속도제한 | slowapi |
| 모니터링 | Prometheus, prometheus-fastapi-instrumentator |
| 컨테이너 | Docker (python:3.10-bookworm) |
| 한글 폰트 | NanumGothic, Noto Color Emoji |

---

## 환경변수

| 변수명 | 설명 | 기본값 |
|---|---|---|
| `S3_BUCKET_NAME` | 변환 결과물을 저장할 S3 버킷 이름 | `sixsense-pdf-storage` |

S3 인증은 EC2 IAM 인스턴스 프로파일을 통해 자동으로 처리됩니다. 별도의 액세스 키 설정이 필요하지 않습니다.

---

## 실행 방법

### Docker

```bash
docker build -t sixsense-converter .
docker run -p 8000:8000 \
  -e S3_BUCKET_NAME=your-bucket-name \
  sixsense-converter
```

### 로컬 (개발 환경)

LibreOffice, Ghostscript, xvfb 등 시스템 의존성이 사전 설치되어 있어야 합니다.

```bash
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

---

## API 명세

### `POST /convert-single/`

단일 파일을 PDF로 변환합니다.

- **Rate Limit:** 10회 / 분
- **Content-Type:** `multipart/form-data`

| 파라미터 | 타입 | 필수 | 설명 |
|---|---|---|---|
| `file` | File | ✅ | 변환할 파일 |
| `wm_type` | string | ❌ | 워터마크 종류 (`text` \| `image` \| `none`) |
| `wm_text` | string | ❌ | 텍스트 워터마크 내용 |
| `wm_image` | File | ❌ | 이미지 워터마크 파일 |

**응답**
```json
{ "download_url": "https://s3.amazonaws.com/..." }
```

---

### `POST /convert-merge/`

여러 파일을 하나의 PDF로 병합합니다.

- **Rate Limit:** 5회 / 분
- **Content-Type:** `multipart/form-data`
- **최대 파일 수:** 10개

| 파라미터 | 타입 | 필수 | 설명 |
|---|---|---|---|
| `files` | File[] | ✅ | 병합할 파일 목록 |
| `wm_type` | string | ❌ | 워터마크 종류 (`text` \| `image` \| `none`) |
| `wm_text` | string | ❌ | 텍스트 워터마크 내용 |
| `wm_image` | File | ❌ | 이미지 워터마크 파일 |

**응답**
```json
{ "download_url": "https://s3.amazonaws.com/..." }
```

---

### `GET /health`

컨테이너 생존 여부를 확인합니다 (Liveness Probe).

### `GET /ready`

서비스 준비 상태를 확인합니다 (Readiness Probe). 스토리지 쓰기 권한 및 환경변수 로드 여부를 점검합니다.

### `GET /metrics`

Prometheus 메트릭 엔드포인트입니다.

---

## 변환 파이프라인

```
파일 업로드
    │
    ▼
파일 형식 판별
    ├─ 이미지 (png/jpg/bmp) ──→ Pillow → PDF 조각
    └─ 문서 (docx/txt/hwp) ──→ LibreOffice (xvfb-run) → PDF 조각
    │
    ▼
pikepdf로 PDF 조각 병합
    │
    ▼
ReportLab으로 워터마크 합성 (선택)
    │
    ▼
Ghostscript로 PDF 압축
    │
    ▼
AWS S3 업로드 → Pre-signed URL 발급 (유효시간 5분)
    │
    ▼
임시 파일 전량 삭제
```

---

## 보안 고려사항

- 변환에 사용된 임시 파일은 처리 완료 즉시 삭제됩니다.
- Pre-signed URL은 발급 후 **5분 뒤 자동 만료**됩니다.
- LibreOffice 실행 시 매 요청마다 **독립된 사용자 프로필**을 생성하여 설정 충돌 및 정보 유출을 방지합니다.
- Rate Limiter를 통해 클라이언트 IP 기반 요청 횟수를 제한합니다.

---

## 지원 파일 형식

| 형식 | 변환 엔진 | 비고 |
|---|---|---|
| `docx` | LibreOffice | |
| `xlsx` | LibreOffice | |
| `pptx` | LibreOffice | |
| `txt` | LibreOffice | UTF-8 인코딩 보정 적용 |
| `hwp` | LibreOffice | |
| `png` / `jpg` / `jpeg` | Pillow | |
| `bmp` | Pillow | RGB 변환 후 처리 |

> LibreOffice가 지원하는 형식이라면 위 목록 외의 파일도 변환될 수 있습니다 (`odt`, `ppt`, `xls` 등).
