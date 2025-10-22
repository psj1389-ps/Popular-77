FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libreoffice \
    libreoffice-writer \
    libreoffice-calc \
    libreoffice-impress \
    fonts-liberation \
    fonts-dejavu-core \
    fonts-noto \
    fonts-noto-cjk \
    fonts-noto-color-emoji \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy services directory
COPY services/ /app/services/

# Copy entrypoint script
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Install Python dependencies for all services
RUN find /app/services -name "requirements.txt" -exec pip install --root-user-action=ignore -r {} \;

# Expose port
EXPOSE 10000

# Set entrypoint
CMD ["/entrypoint.sh"]