#!/bin/bash

# Render 빌드 스크립트 - LibreOffice 설치 및 설정

echo "Starting build process..."

# 환경 변수 설정
export DEBIAN_FRONTEND=noninteractive

# 시스템 패키지 업데이트
echo "Updating package lists..."
apt-get update -y

# 필수 패키지 먼저 설치
echo "Installing essential packages..."
apt-get install -y \
    wget \
    gnupg \
    software-properties-common \
    ca-certificates

# LibreOffice 및 필수 패키지 설치
echo "Installing LibreOffice and dependencies..."
apt-get install -y \
    libreoffice \
    libreoffice-writer \
    libreoffice-calc \
    libreoffice-impress \
    libreoffice-common \
    fonts-dejavu \
    fonts-liberation \
    fonts-noto \
    fonts-noto-cjk \
    fonts-noto-color-emoji \
    fonts-nanum

# PATH에 LibreOffice 바이너리 경로 추가
echo "Setting up LibreOffice PATH..."
export PATH="/usr/bin:/usr/local/bin:/opt/libreoffice*/program:$PATH"

# 심볼릭 링크 생성 (필요한 경우)
echo "Creating symbolic links..."
if [ ! -f /usr/bin/soffice ] && [ -f /usr/lib/libreoffice/program/soffice ]; then
    ln -sf /usr/lib/libreoffice/program/soffice /usr/bin/soffice
fi

# LibreOffice 설치 확인
echo "Verifying LibreOffice installation..."
echo "Checking possible LibreOffice locations..."
find /usr -name "soffice" -type f 2>/dev/null || echo "No soffice found in /usr"
find /opt -name "soffice" -type f 2>/dev/null || echo "No soffice found in /opt"

# 다양한 경로에서 soffice 확인
SOFFICE_PATHS=(
    "/usr/bin/soffice"
    "/usr/lib/libreoffice/program/soffice"
    "/opt/libreoffice*/program/soffice"
)

SOFFICE_FOUND=""
for path in "${SOFFICE_PATHS[@]}"; do
    if [ -f "$path" ] || ls $path 1> /dev/null 2>&1; then
        SOFFICE_FOUND="$path"
        echo "Found soffice at: $path"
        break
    fi
done

if [ -n "$SOFFICE_FOUND" ]; then
    echo "LibreOffice installed successfully"
    $SOFFICE_FOUND --version || echo "Version check failed but binary exists"
    
    # 실행 권한 확인 및 설정
    chmod +x "$SOFFICE_FOUND"
    
    # 환경 변수 파일에 PATH 저장
    echo "export PATH=\"/usr/bin:/usr/local/bin:/usr/lib/libreoffice/program:\$PATH\"" > /app/.profile
else
    echo "ERROR: LibreOffice installation failed - soffice binary not found"
    echo "Available LibreOffice packages:"
    dpkg -l | grep libreoffice || echo "No LibreOffice packages found"
    exit 1
fi

# Python 의존성 설치
echo "Installing Python dependencies..."
pip install -r requirements.txt

echo "Build completed successfully!"
echo "LibreOffice binary location: $SOFFICE_FOUND"