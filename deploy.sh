#!/bin/bash

# 1. 기존 컨테이너 정리
echo "Cleaning up old container..."
# 실행 중인 컨테이너가 있으면 멈추고 삭제 (이름 기준)
sudo docker stop sixsense-final-test 2>/dev/null
sudo docker rm sixsense-final-test 2>/dev/null

# 2. 도커 이미지 빌드
echo "Building Docker image..."
# 캐시를 적절히 활용하되 소스 변경사항을 반영하여 빌드
sudo docker build -t doc-converter:latest .

# 3. 환경 설정 및 컨테이너 실행
# .env 파일이 있으면 로드하고, 없으면 IAM Role 기반으로 실행합니다
echo "Starting container..."

if [ -f .env ]; then
    echo "Found .env file. Starting with environment variables..."
    sudo docker run -d \
      -p 8000:8000 \
      --env-file .env \
      --name sixsense-final-test \
      doc-converter:latest
else
    echo "No .env file found. Starting with IAM Role and internal defaults..."
    # .env가 없을 때는 --env-file 옵션을 제외해야 실행 에러가 나지 않습니다
    sudo docker run -d \
      -p 8000:8000 \
      --name sixsense-final-test \
      doc-converter:latest
fi

# 4. 로그 실시간 확인
echo "Showing real-time logs (Press CTRL+C to detach)..."
sudo docker logs -f sixsense-final-test
