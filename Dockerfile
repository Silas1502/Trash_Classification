FROM python:3.11-slim

# Cài đặt các thư viện hệ thống cần thiết cho OpenCV (libgl1, libglib)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Tạo user không có đặc quyền root (Chuẩn bảo mật của Hugging Face Spaces: UID 1000)
RUN useradd -m -u 1000 user
USER user
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH \
    PORT=7860 \
    PYTHONUNBUFFERED=1

WORKDIR $HOME/app

# Cài đặt các dependencies Python
COPY --chown=user:user backend/requirements.txt requirements.txt
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy mã nguồn Backend vào container
COPY --chown=user:user backend/app ./app
COPY --chown=user:user backend/app/core/safety_thresholds.json ./app/core/safety_thresholds.json

# Cổng mặc định của Hugging Face Spaces là 7860
EXPOSE 7860

# Khởi chạy FastAPI Uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "7860"]
