import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = ROOT_DIR / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

import gradio as gr
from app.main import create_app

# Khởi tạo ứng dụng FastAPI
fastapi_app = create_app()

# Giao diện thông tin trạng thái trên trang chủ Hugging Face Space
with gr.Blocks(title="Trash Classification API") as demo:
    gr.Markdown("# ♻️ Trash Classification System - Backend API")
    gr.Markdown("""
    ### FastAPI Backend đang hoạt động ổn định trên Hugging Face Spaces (16 GB RAM Free)!
    
    * 📖 **Tài liệu API tương tác (Swagger UI):** [Mở /docs](/docs)
    * 🔍 **Kiểm tra trạng thái (Health Check):** [/api/v1/health](/api/v1/health)
    * 🌐 **Giao diện người dùng:** Next.js Frontend trên Vercel
    """)

# Gắn Gradio lên FastAPI app
app = gr.mount_gradio_app(fastapi_app, demo, path="/")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7860)
