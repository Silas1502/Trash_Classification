import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = ROOT_DIR / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

import gradio as gr
import spaces
from app.main import create_app

# ZeroGPU quét hàm này khi khởi động và yêu cầu demo.queue()
@spaces.GPU
def check_status(dummy: str = "ping") -> str:
    return "Trash Classification Backend is Online & Ready with ZeroGPU!"

# Giao diện Gradio Interface để ZeroGPU supervisor nhận diện 100%
demo = gr.Interface(
    fn=check_status,
    inputs=gr.Textbox(label="API Status Check", value="ping"),
    outputs=gr.Textbox(label="Response"),
    title="♻️ Trash Classification System - Backend API",
    description="FastAPI Backend đang hoạt động ổn định trên Hugging Face Spaces (16 GB RAM)!\n- Swagger UI Docs: /docs\n- Health Check: /api/v1/health\n- Frontend: Next.js on Vercel"
)
demo.queue()

# Khởi tạo FastAPI app và gắn Gradio
fastapi_app = create_app()
app = gr.mount_gradio_app(fastapi_app, demo, path="/")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7860)
