FROM python:3.12-slim

# LibreOffice + 폰트 설치
RUN apt-get update && apt-get install -y --no-install-recommends \
    libreoffice-writer libreoffice-calc libreoffice-impress \
    fonts-dejavu fonts-liberation fonts-noto fonts-noto-cjk fonts-noto-color-emoji \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 의존성 설치
COPY services/docx-pdf/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 앱 소스 복사
COPY services/docx-pdf/ /app/

ENV PORT=10000
CMD ["python", "-m", "gunicorn", "-b", "0.0.0.0:10000", "-t", "600", "-k", "gthread", "--threads", "2", "-w", "1", "app:app"]