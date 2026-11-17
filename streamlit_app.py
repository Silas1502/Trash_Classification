from contextlib import contextmanager
import hashlib
import mimetypes
import os
from pathlib import Path
import shutil
import sys
from tempfile import TemporaryDirectory
from threading import Event, Lock, Thread
from time import perf_counter
from zipfile import BadZipFile, ZipFile


CGROUP_ROOT = Path("/sys/fs/cgroup")
UNLIMITED = 1 << 60
MIB = 1024**2
GIB = 1024**3
GROUP_SIZE = 4
IMAGE_COUNT = 20
CHECKPOINT_SHA256 = "866206ad9084f8feba2d67ccb550ac76965a8ce7316256ec0560a676f7b1e7a8"


def read_counter(path):
    try:
        return int(path.read_text().strip())
    except (OSError, ValueError):
        return None


def memory_budget(root=CGROUP_ROOT, proc_cgroup=Path("/proc/self/cgroup")):
    try:
        memberships = [line.split(":", 2) for line in proc_cgroup.read_text().splitlines()]
    except OSError:
        memberships = []

    readings = []
    for controllers, mount, limit_file, used_file in (
        ("", root, "memory.max", "memory.current"),
        ("memory", root / "memory", "memory.limit_in_bytes", "memory.usage_in_bytes"),
    ):
        group = next(
            (entry[2] for entry in memberships if len(entry) == 3 and controllers in entry[1].split(",")),
            "/",
        )
        directory = (mount / group.lstrip("/")).resolve()
        mount = mount.resolve()
        if not directory.is_relative_to(mount):
            continue
        for parent in (directory, *directory.parents):
            if not parent.is_relative_to(mount):
                break
            limit = read_counter(parent / limit_file)
            used = read_counter(parent / used_file)
            if limit is not None and 0 < limit < UNLIMITED and used is not None and used >= 0:
                readings.append((limit, used))

    if not readings:
        return None
    limit, used = min(readings, key=lambda value: value[0])
    headroom = max(0, min(capacity - usage for capacity, usage in readings))
    return limit, used, headroom


@contextmanager
def track_memory():
    used_samples = []
    free_samples = []
    stop = Event()

    def sample():
        reading = memory_budget()
        if reading is not None:
            _, used, free = reading
            used_samples.append(used)
            free_samples.append(free)

    def watch():
        while not stop.wait(0.1):
            sample()

    sample()
    thread = Thread(target=watch, daemon=True)
    thread.start()
    try:
        yield used_samples, free_samples
    finally:
        stop.set()
        thread.join()
        sample()


def report_group(stage, seconds, memory, count):
    used, free = memory
    return {
        "Bước": stage,
        "Ảnh hoàn tất": count,
        "Thời gian (giây)": round(seconds, 2),
        "RAM đỉnh (GiB)": round(max(used) / GIB, 3) if used else None,
        "RAM trống thấp nhất (GiB)": round(min(free) / GIB, 3) if free else None,
    }


def run_benchmark(checkpoint_file, image_zip, update_progress):
    from io import BytesIO

    from PIL import Image

    # The standalone cloud branch has app/ beside this script.
    if not Path(__file__).with_name("app").is_dir():
        sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "backend"))
    os.environ.setdefault("KERAS_BACKEND", "tensorflow")
    os.environ.setdefault("TF_NUM_INTRAOP_THREADS", "2")
    os.environ.setdefault("TF_NUM_INTEROP_THREADS", "1")

    checkpoint_file.seek(0)
    if hashlib.file_digest(checkpoint_file, "sha256").hexdigest() != CHECKPOINT_SHA256:
        raise ValueError("Hãy chọn đúng checkpoint dự đoán 119 MB của dự án.")
    checkpoint_file.seek(0)
    image_zip.seek(0)
    with TemporaryDirectory() as temporary, ZipFile(image_zip) as archive:
        entries = [entry for entry in archive.infolist() if not entry.is_dir()]
        mime_types = [mimetypes.guess_type(entry.filename)[0] for entry in entries]
        if len(entries) != IMAGE_COUNT or any(
            not 0 < entry.file_size <= 8 * MIB or mime not in {"image/jpeg", "image/png", "image/webp"}
            for entry, mime in zip(entries, mime_types, strict=True)
        ):
            raise ValueError("ZIP cần chứa đúng 20 ảnh JPG, PNG hoặc WebP, tối đa 8 MiB mỗi ảnh.")

        checkpoint = Path(temporary) / "best_v2_convnext_retrained.keras"
        with checkpoint.open("wb") as target:
            shutil.copyfileobj(checkpoint_file, target, length=MIB)

        started = perf_counter()
        with track_memory() as memory:
            from app.core.config import Settings
            from app.core.safety_gate import SafetyFilter
            from app.ml.inference import classify_batch
            from app.ml.model_loader import ModelBundle, load_model
            from app.ml.preprocessor import ImagePreprocessor

            settings = Settings(
                _env_file=None, model_path=checkpoint, tta_views="5",
                adaptive_assessment_enabled=False, smart_crop=False,
            )
            safety = SafetyFilter.load(settings.thresholds_path)
            model = load_model(settings, safety.thresholds.classes.labels)
            if not isinstance(model, ModelBundle):
                raise RuntimeError("Không nạp được checkpoint dự đoán.")
            processor = ImagePreprocessor(settings.max_image_pixels, settings.smart_crop)
        report = [report_group("Nạp TensorFlow và mô hình", perf_counter() - started, memory, 0)]

        for start in range(0, IMAGE_COUNT, GROUP_SIZE):
            group = entries[start:start + GROUP_SIZE]
            started = perf_counter()
            with track_memory() as memory:
                for index, entry in enumerate(group, start=start):
                    image = processor.prepare(archive.read(entry), mime_types[index])
                    [result] = classify_batch(model, [image], settings, safety)
                    if result.xai is None:
                        raise RuntimeError(f"Ảnh {index + 1} thiếu kết quả giải thích.")
                    for overlay in (result.xai.gradcam_jpeg, result.xai.spatial_energy_jpeg):
                        with Image.open(BytesIO(overlay)) as decoded:
                            if decoded.format != "JPEG" or decoded.size != (320, 320):
                                raise RuntimeError(f"Ảnh giải thích {index + 1} sai định dạng.")
                            decoded.verify()
                    update_progress(index + 1)
            report.append(report_group(f"Lượt {start // GROUP_SIZE + 1}", perf_counter() - started, memory, len(group)))
        return report


def main():
    import streamlit as st

    st.set_page_config(page_title="Đo RAM Streamlit")
    st.title("Đo RAM Streamlit")
    st.button("Đo lại")
    reading = memory_budget()
    if reading is None:
        st.warning("Môi trường chưa cung cấp số liệu giới hạn RAM có thể đọc được.")
        return

    for column, label, value in zip(
        st.columns(3),
        ("Giới hạn RAM đọc được", "RAM đang dùng", "RAM còn trống"),
        reading,
        strict=True,
    ):
        column.metric(label, f"{value / GIB:.2f} GiB")
    st.caption("Ứng dụng chỉ đọc số liệu bộ nhớ của container Linux.")

    st.header("Kiểm thử 20 ảnh")
    checkpoint_file = st.file_uploader("Checkpoint dự đoán", type="keras")
    image_zip = st.file_uploader("ZIP gồm 20 ảnh mẫu", type="zip")

    @st.cache_resource
    def benchmark_lock():
        return Lock()

    if st.button("Chạy 5 lượt", disabled=checkpoint_file is None or image_zip is None):
        lock = benchmark_lock()
        if not lock.acquire(blocking=False):
            st.warning("Đang có một lượt kiểm thử chạy.")
        else:
            progress = st.progress(0, text="Đang nạp mô hình")
            st.session_state.pop("benchmark_report", None)
            try:
                st.session_state.benchmark_report = run_benchmark(
                    checkpoint_file,
                    image_zip,
                    lambda done: progress.progress(done / IMAGE_COUNT, text=f"Đã kiểm tra {done}/{IMAGE_COUNT} ảnh"),
                )
            except (BadZipFile, OSError, RuntimeError, ValueError) as error:
                st.error(str(error))
            finally:
                lock.release()

    if report := st.session_state.get("benchmark_report"):
        st.success("20/20 ảnh có cả Grad-CAM và Spatial Energy.")
        st.table(report)


if __name__ == "__main__":
    main()
