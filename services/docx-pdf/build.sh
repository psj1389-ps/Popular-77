#!/bin/bash

# Render 빌드 스크립트 - LibreOffice 설치 및 설정

echo "Starting build process..."

# 시스템 패키지 업데이트
echo "Updating package lists..."
apt-get update

# LibreOffice 및 필수 패키지 설치
echo "Installing LibreOffice and dependencies..."
apt-get install -y \
    libreoffice \
    libreoffice-writer \
    libreoffice-calc \
    libreoffice-impress \
    fonts-dejavu \
    fonts-liberation \
    fonts-noto \
    fonts-noto-cjk \
    fonts-noto-color-emoji \
    fonts-nanum

# LibreOffice 설치 확인
echo "Verifying LibreOffice installation..."
if command -v soffice &> /dev/null; then
    echo "LibreOffice installed successfully"
    soffice --version
else
    echo "ERROR: LibreOffice installation failed"
    exit 1
fi

# Python 의존성 설치
echo "Installing Python dependencies..."
pip install -r requirements.txt

echo "Build completed successfully!"