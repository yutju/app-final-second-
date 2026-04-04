# SixSense Doc-Converter

> **단 한 번의 드래그로, 모든 문서를 완벽한 PDF로**  
> DevSecOps 기반 클라우드 네이티브 문서 변환 서비스

---

## 📌 프로젝트 개요

SixSense Doc-Converter는 다양한 문서 포맷을 PDF로 변환하고, 워터마크 삽입 · 다중 파일 병합 · 비밀번호 암호화 · S3 보안 스토리지 연동까지 제공하는 통합 변환 서비스입니다.  
모든 인프라는 **Terraform IaC**로 관리되며, **GitHub Actions CI/CD** 파이프라인에서 **Trivy + Checkov** 보안 스캐닝을 자동 수행합니다.

---

## 🚀 주요 기능

| 기능 | 설명 |
|------|------|
| 단일 파일 변환 | DOCX, XLSX, PPTX, TXT, HWP, PNG, JPG, BMP → PDF |
| 다중 파일 병합 | 최대 10개 파일을 순서 지정 후 하나의 PDF로 병합 |
| 텍스트 워터마크 | 위치 · 크기 · 투명도 · 회전 각도 커스터마이징 |
| 이미지 워터마크 | 로고 PNG/JPG 업로드, 동일한 커스터마이징 옵션 지원 |
| 페이지 번호 삽입 | `- Page N / Total -` 형식으로 하단 자동 삽입 |
| PDF 비밀번호 암호화 | AES-128(R=4) 기반 열기 비밀번호 설정 |
| S3 보안 스토리지 | 변환 결과물을 S3에 격리 저장, IAM Pre-signed URL(5분) 발급 후 자동 파기 |
| Rate Limiting | 단일 변환 10req/min, 병합 변환 5req/min |

---

## 🗂️ 프로젝트 구조

```
.
├── main.py              # FastAPI 앱 진입점, 라우팅, S3 업로드
├── processor.py         # PDF 변환·병합·워터마크 처리 엔진
├── converter.py         # LibreOffice 래퍼 (xvfb-run 기반 headless 변환)
├── templates.py         # 프론트엔드 HTML/CSS/JS (인라인 Single Page)
├── components.py        # About 섹션, API 문서 섹션 HTML 컴포넌트
├── requirements.txt     # Python 패키지 목록
├── Dockerfile           # 컨테이너 빌드 정의
├── static/
│   ├── sixsenselogo.png # 서비스 로고
│   └── convert.png      # 변환 완료 아이콘
└── temp_storage/        # 변환 임시 파일 (자동 생성 · 자동 정리)
```

---

## ⚙️ 기술 스택

### Backend
- **Python 3.10** / **FastAPI** — 비동기 API 서버
- **LibreOffice** (xvfb-run headless) — DOCX/XLSX/PPTX/HWP → PDF 변환
- **Ghostscript** — 다중 PDF 병합
- **pikepdf** — 워터마크 오버레이, PDF 암호화
- **ReportLab** — 워터마크 레이어 생성
- **Pillow** — 이미지 전처리 (모드 정규화, PNG 변환)
- **boto3** — AWS S3 업로드 및 Pre-signed URL 생성
- **slowapi** — Rate Limiting

### Frontend
- **Vanilla JS** (Axios, SortableJS) — 드래그&드롭, 파일 순서 변경
- **Tailwind CSS** — UI 스타일링
- **Canvas API** — 워터마크 실시간 A4 미리보기

### Infrastructure
- **Docker** — 컨테이너 기반 배포
- **AWS EC2** — 애플리케이션 서버
- **AWS S3 + IAM** — 결과물 보안 스토리지 및 Pre-signed URL
- **Terraform** — IaC 인프라 관리
- **GitHub Actions** — CI/CD 파이프라인
- **Trivy + Checkov** — 이미지 및 코드 보안 스캐닝
- **WAF (ModSecurity)** — 악성 웹 요청 차단
- **Snort IDS / netfilter IPS** — 네트워크 침입 탐지 및 차단
- **Falco** — 쿠버네티스 런타임 보안 감시
- **Kafka** — 보안 이벤트 로그 실시간 백업
- **Prometheus + Grafana** — 서비스 모니터링

---

## 📦 설치 및 실행

### 사전 요구사항
- Docker
- AWS 자격증명 (IAM Role 또는 `.env` 파일)

### 환경변수 설정

`.env` 파일을 프로젝트 루트에 생성합니다.

```env
S3_BUCKET_NAME=your-s3-bucket-name
AWS_DEFAULT_REGION=ap-northeast-2
```

IAM Role이 EC2에 연결돼 있으면 별도 키 설정 없이 자동 인증됩니다.

### Docker로 실행

```bash
# 이미지 빌드
docker build -t doc-converter .

# 컨테이너 실행
docker run -d \
  --name sixsense-converter \
  --env-file .env \
  -p 8000:8000 \
  doc-converter
```

### 접속

```
http://localhost:8000
```

---

## 🔌 API 명세

### `POST /convert-single/`

단일 파일을 PDF로 변환합니다.

| 파라미터 | 타입 | 필수 | 설명 |
|----------|------|------|------|
| `file` | File | ✅ | 변환할 파일 |
| `wm_type` | string | | `none` / `text` / `image` (기본: `none`) |
| `wm_text` | string | | 텍스트 워터마크 문구 |
| `wm_image` | File | | 이미지 워터마크 파일 |
| `wm_position` | string | | `center` / `top-left` / `top-right` / `bottom-left` / `bottom-right` |
| `wm_size` | float | | 워터마크 크기 (기본: 60.0) |
| `wm_opacity` | float | | 투명도 0.0~1.0 (기본: 0.3) |
| `wm_rotation` | float | | 회전 각도 (기본: 45.0) |
| `pdf_pw` | string | | PDF 열기 비밀번호 |
| `use_pg_num` | bool | | 페이지 번호 삽입 여부 (기본: false) |

**Rate Limit:** 10 req/min

---

### `POST /convert-merge/`

여러 파일을 병합하여 하나의 PDF로 변환합니다.

| 파라미터 | 타입 | 필수 | 설명 |
|----------|------|------|------|
| `files` | File[] | ✅ | 병합할 파일 배열 |
| 나머지 파라미터 | | | `/convert-single/`과 동일 |

**Rate Limit:** 5 req/min

---

**응답 예시**

```json
{
  "download_url": "https://s3.amazonaws.com/bucket/output/uuid.pdf?X-Amz-..."
}
```

> Pre-signed URL은 발급 후 **5분간 유효**하며 이후 자동 만료됩니다.

---

## 🛡️ 보안 설계

- 업로드 파일은 `temp_storage/`에 UUID 파일명으로 저장되며 변환 완료 후 **즉시 삭제**됩니다.
- 변환 결과 PDF는 S3에 `output/{uuid}.pdf` 경로로 격리 저장됩니다.
- Pre-signed URL은 **300초(5분) 후 만료**되며 이후 접근이 불가합니다.
- PDF 암호화는 **AES-128 (PDF R=4)** 표준을 사용합니다.
- LibreOffice 변환은 요청마다 **독립 UserInstallation 프로필**을 생성하여 설정 충돌을 방지합니다.

---

## 🐳 Dockerfile 주요 설정

| 항목 | 내용 |
|------|------|
| 베이스 이미지 | `python:3.10-bookworm` |
| 한국어 폰트 | `fonts-nanum`, `fonts-nanum-extra` 설치 |
| 폰트 대체 규칙 | 맑은 고딕 → NanumGothic, Segoe UI Emoji → Noto Color Emoji |
| 가상 디스플레이 | `xvfb` + `xauth` (LibreOffice headless 그래픽 렌더링) |
| PDF 병합 | `ghostscript` |
| 포트 | `8000` |

---

## 📋 지원 파일 형식

| 분류 | 확장자 |
|------|--------|
| 문서 | `.docx`, `.xlsx`, `.pptx`, `.txt`, `.hwp` |
| 이미지 | `.png`, `.jpg`, `.jpeg`, `.bmp` |
| 최대 파일 크기 | 50MB |
| 최대 병합 파일 수 | 10개 |

---

## 📄 라이선스

© 2026 SixSense Project | Built for Infrastructure Engineers
