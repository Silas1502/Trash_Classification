import os
import sys
from importlib.metadata import version
from io import BytesIO
from pathlib import Path

os.environ["KERAS_BACKEND"] = "torch"
sys.path.insert(0, str(Path(__file__).resolve().parent / "backend"))

# Import Spaces before PyTorch or Keras so ZeroGPU can prepare its CUDA runtime.
import spaces
import gradio as gr
import keras
import numpy as np
import tensorflow as tf
from fastapi import Request
from gradio.context import LocalContext
from PIL import Image
from spaces import zero as spaces_zero

from app.core.config import Settings
from app.core.safety_gate import SafetyFilter
from app.main import create_app
from app.ml.inference import InferenceResult, classify_batch
from app.ml.model_loader import DummyPredictor, ModelBundle, load_model
from app.ml.preprocessor import IMAGE_TYPES, InvalidImage, PreparedImage, area_resize
from app.ml.torch_inference import classify_with_torch

settings = Settings()
safety = SafetyFilter.load(settings.thresholds_path)
with keras.device("cpu"):
    model = load_model(settings, safety.thresholds.classes.labels)

device = "cuda" if os.getenv("SPACES_ZERO_GPU", "").lower() in {"1", "t", "true"} else "cpu"
if device == "cuda":
    if isinstance(model, DummyPredictor):
        raise RuntimeError("Configure MODEL_PATH or MODEL_DOWNLOAD_URL and MODEL_SHA256 before starting ZeroGPU.")
    for network in (model.sub_logits_model, model.spatial, model.head):
        network.to("cuda")


def prepare_tensors(images: list[PreparedImage]) -> tuple[np.ndarray, np.ndarray]:
    # Keep the TensorFlow area resize in the parent process and send arrays to the GPU worker.
    rgb = tf.stack([image.model_rgb for image in images])
    zoom = area_resize(rgb[:, 16:304, 16:304, :]).numpy() if settings.tta_views == "5" else np.empty(0)
    return rgb.numpy(), zoom


@spaces.GPU(duration=35)
def predict_images(rgb: np.ndarray, zoom: np.ndarray) -> list[InferenceResult]:
    if isinstance(model, DummyPredictor):
        raise gr.Error("Chưa cấu hình checkpoint của mô hình.")
    with keras.device(device):
        return classify_with_torch(model, rgb, zoom, safety, settings.adaptive_assessment_enabled)


def classify_for_space(
    bundle: ModelBundle | DummyPredictor, images: list[PreparedImage], config: Settings, gate: SafetyFilter,
) -> list[InferenceResult]:
    if isinstance(bundle, DummyPredictor):
        return classify_batch(bundle, images, config, gate)
    return predict_images(*prepare_tensors(images))


def prepare_demo_image(contents: bytes | None) -> tuple[np.ndarray, np.ndarray]:
    if not contents or len(contents) > settings.max_upload_bytes:
        raise gr.Error("Chọn ảnh nằm trong giới hạn kích thước tải lên.")
    try:
        with Image.open(BytesIO(contents), formats=list(IMAGE_TYPES)) as image:
            mime = IMAGE_TYPES[image.format][0]
        return prepare_tensors([fastapi_app.state.preprocessor.prepare(contents, mime)])
    except (OSError, InvalidImage, Image.DecompressionBombError) as exc:
        raise gr.Error("Chỉ hỗ trợ ảnh JPEG, PNG hoặc WebP hợp lệ.") from exc


def show_demo_result(results: list[InferenceResult]):
    result, = results
    return (
        result.decision.waste_type,
        np.asarray(Image.open(BytesIO(result.xai.gradcam_jpeg))),
        np.asarray(Image.open(BytesIO(result.xai.spatial_energy_jpeg))),
    )


with gr.Blocks(title="Phân loại rác") as demo:
    image = gr.File(label="Ảnh cần phân loại", file_types=["image"], type="binary")
    button = gr.Button("Bắt đầu dự đoán")
    label = gr.Textbox(label="Loại rác")
    gradcam = gr.Image(label="Grad-CAM")
    spatial_energy = gr.Image(label="Spatial Energy")
    rgb, zoom, results = gr.State(), gr.State(), gr.State()
    button.click(prepare_demo_image, image, [rgb, zoom], api_visibility="private").success(
        predict_images, [rgb, zoom], results, api_visibility="private",
    ).success(show_demo_result, results, [label, gradcam, spatial_energy], api_visibility="private")

fastapi_app = create_app(settings, model=model, batch_classifier=classify_for_space)

if device == "cuda" and not hasattr(spaces_zero, "ZeroGPUMiddleware"):
    @fastapi_app.middleware("http")
    async def forward_zerogpu_request(request: Request, call_next):
        token = LocalContext.request.set(gr.Request(request=request))
        try:
            return await call_next(request)
        finally:
            LocalContext.request.reset(token)

app = gr.mount_gradio_app(
    fastapi_app, demo.queue(), path="/", ssr_mode=False,
    blocked_paths=["/models"], max_file_size=settings.max_upload_bytes,
)

if __name__ == "__main__":
    import uvicorn

    print(f"Spaces {version('spaces')}, Gradio {gr.__version__}, inference device: {device}; "
          f"GPU callback registered: {hasattr(predict_images, 'zerogpu')}", flush=True)
    if device == "cuda" and not hasattr(spaces_zero, "ZeroGPUMiddleware"):
        # Spaces 0.51 only calls its startup hook from Blocks.launch. This Space mounts Blocks on FastAPI.
        spaces_zero.startup()
    uvicorn.run(app, host="0.0.0.0", port=7860)
