FROM python:3.10-bookworm

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV LANG=ko_KR.UTF-8
ENV LC_ALL=ko_KR.UTF-8
ENV TZ=Asia/Seoul

RUN apt-get update && apt-get install -y \
    libreoffice libreoffice-writer libreoffice-calc libreoffice-math \
    libreoffice-l10n-ko libreoffice-java-common default-jre \
    # 🔥 표 렌더링을 위한 그래픽 라이브러리 추가
    libxrender1 libxtst6 libxi6 libgl1-mesa-dri libglu1-mesa \
    xvfb x11-utils dbus-x11 libqpdf-dev qpdf fontconfig \
    # 🔥 MS Office 표 너비 대응 필수 폰트
    fonts-nanum fonts-nanum-extra fonts-noto-cjk fonts-liberation2 \
    fonts-noto-color-emoji fonts-symbola \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# 폰트 매핑 설정 (맑은 고딕 등을 나눔고딕으로 연결)
RUN mkdir -p /etc/fonts/conf.d && \
    echo '<?xml version="1.0"?><!DOCTYPE fontconfig SYSTEM "fonts.dtd"><fontconfig>\
    <match target="pattern"><test qual="any" name="family"><string>Segoe UI Emoji</string></test><edit name="family" mode="assign" binding="same"><string>Noto Color Emoji</string></edit></match>\
    <match target="pattern"><test name="family"><string>맑은 고딕</string></test><edit name="family" mode="assign" binding="same"><string>NanumGothic</string></edit></match>\
    <match target="pattern"><test name="family"><string>Malgun Gothic</string></test><edit name="family" mode="assign" binding="same"><string>NanumGothic</string></edit></match>\
    <match target="pattern"><test name="family"><string>굴림</string></test><edit name="family" mode="assign" binding="same"><string>NanumGothic</string></edit></match>\
    </fontconfig>' > /etc/fonts/conf.d/99-msfonts.conf

RUN fc-cache -fv

# LibreOffice 전역 설정 (표 선 누락 방지)
RUN mkdir -p /root/.config/libreoffice/4/user && \
    echo '<?xml version="1.0" encoding="UTF-8"?><oor:items xmlns:oor="http://openoffice.org/2001/registry" xmlns:xs="http://www.w3.org/2001/XMLSchema"><item oor:path="/org.openoffice.Office.Common/Layout"><prop oor:name="IsKernAsianPunctuation" oor:op="fuse"><value>true</value></prop></item></oor:items>' > /root/.config/libreoffice/4/user/registrymodifications.xcu

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN mkdir -p /app/temp_storage

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers"]
