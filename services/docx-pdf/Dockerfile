FROM python:3.11-slim

# 시스템 패키지 설치 (LibreOffice 및 폰트)
RUN apt-get update && apt-get install -y \
    libreoffice \
    fonts-liberation \
    fonts-dejavu-core \
    fontconfig \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# 작업 디렉토리 설정
WORKDIR /app

# Python 의존성 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 애플리케이션 파일 복사
COPY . .

# 포트 설정
EXPOSE 10000

# 메모리 제한 설정 (환경 변수)
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV MALLOC_TRIM_THRESHOLD_=100000
ENV MALLOC_MMAP_THRESHOLD_=100000

# gunicorn을 사용한 프로덕션 실행
CMD ["sh", "-c", "exec python -m gunicorn app:app -b 0.0.0.0:${PORT:-10000} -k sync -w 1 --threads 1 --timeout 900 --graceful-timeout 60 --keep-alive 30 --max-requests 100 --max-requests-jitter 20 --worker-tmp-dir=/dev/shm --worker-connections=50 --limit-request-line=4096 --limit-request-fields=100"]