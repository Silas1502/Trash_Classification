from contextlib import contextmanager
import gc
import hashlib
import json
import mimetypes
import os
from pathlib import Path
import shutil
import sys
from tempfile import TemporaryDirectory
from threading import Event, Lock, Thread
from time import perf_counter, sleep
from zipfile import BadZipFile, ZipFile


CGROUP_ROOT = Path("/sys/fs/cgroup")
UNLIMITED = 1 << 60
MIB = 1024**2
GIB = 1024**3
GROUP_SIZE = 4
IMAGE_COUNT = 20
IDLE_SECONDS = (0, 15, 30)
CHECKPOINT_SHA256 = "866206ad9084f8feba2d67ccb550ac76965a8ce7316256ec0560a676f7b1e7a8"


def read_counter(path):
    try:
        return int(path.read_text().strip())
    except (OSError, ValueError):
        return None


def read_key_values(path):
    try:
        lines = path.read_text().splitlines()
    except OSError:
        return {}
    values = {}
    for line in lines:
        parts = line.split()
        if len(parts) >= 2:
            try:
                values[parts[0].rstrip(":")] = int(parts[1])
            except ValueError:
                continue
    return values


def memory_snapshot(root=CGROUP_ROOT, proc_cgroup=Path("/proc/self/cgroup"),
                    proc_status=Path("/proc/self/status")):
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
                readings.append((limit, used, parent, controllers))

    if not readings:
        return None
    # Read the breakdown from the same cgroup as the reported limit and usage.
    limit, used, directory, controllers = min(readings, key=lambda value: value[0])
    headroom = max(0, min(capacity - usage for capacity, usage, *_ in readings))
    stats = read_key_values(directory / "memory.stat")
    events = read_key_values(directory / "memory.events")
    status = read_key_values(proc_status)
    if controllers == "memory":
        anonymous = stats.get("total_rss", stats.get("rss"))
        file_cache = stats.get("total_cache", stats.get("cache"))
        inactive_file = stats.get("total_inactive_file", stats.get("inactive_file"))
        events = read_key_values(directory / "memory.oom_control")
    else:
        anonymous = stats.get("anon")
        file_cache = stats.get("file")
        inactive_file = stats.get("inactive_file")
    return {
        "limit": limit,
        "used": used,
        "free": headroom,
        "python_rss": status["VmRSS"] * 1024 if "VmRSS" in status else None,
        "anonymous": anonymous,
        "file_cache": file_cache,
        "inactive_file": inactive_file,
        "oom_kill": events.get("oom_kill"),
    }


def memory_budget(root=CGROUP_ROOT, proc_cgroup=Path("/proc/self/cgroup")):
    reading = memory_snapshot(root, proc_cgroup)
    if reading is None:
        return None
    return reading["limit"], reading["used"], reading["free"]


@contextmanager
def track_memory():
    samples = []
    stop = Event()

    def sample():
        reading = memory_snapshot()
        if reading is not None:
            samples.append(reading)

    def watch():
        while not stop.wait(0.1):
            sample()

    sample()
    thread = Thread(target=watch, daemon=True)
    thread.start()
    try:
        yield samples
    finally:
        stop.set()
        thread.join()
        sample()


def report_group(stage, seconds, memory, count):
    used = [sample["used"] for sample in memory]
    free = [sample["free"] for sample in memory]
    python_rss = [sample["python_rss"] for sample in memory if sample["python_rss"] is not None]
    return {
        "Bước": stage,
        "Ảnh hoàn tất": count,
        "Thời gian (giây)": round(seconds, 2),
        "RAM đỉnh (GiB)": round(max(used) / GIB, 3) if used else None,
        "RAM trống thấp nhất (GiB)": round(min(free) / GIB, 3) if free else None,
        "Python RSS đỉnh (GiB)": round(max(python_rss) / GIB, 3) if python_rss else None,
    }


def report_snapshot(stage):
    reading = memory_snapshot()
    if reading is None:
        return {"Mốc đo": stage}
    labels = {
        "used": "Toàn container (GiB)",
        "python_rss": "Python RSS (GiB)",
        "anonymous": "Anonymous container (GiB)",
        "file_cache": "Cache tệp container (GiB)",
        "inactive_file": "Cache tệp inactive (GiB)",
        "free": "RAM trống (GiB)",
    }
    row = {"Mốc đo": stage}
    for key, label in labels.items():
        value = reading[key]
        row[label] = round(value / GIB, 3) if value is not None else None
    row["OOM kill lũy kế"] = reading["oom_kill"]
    return row


def load_benchmark_resources(checkpoint_file):
    # The standalone cloud branch has app/ beside this script.
    if not Path(__file__).with_name("app").is_dir():
        sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "backend"))
    os.environ.setdefault("KERAS_BACKEND", "tensorflow")
    os.environ.setdefault("TF_NUM_INTRAOP_THREADS", "2")
    os.environ.setdefault("TF_NUM_INTEROP_THREADS", "1")

    checkpoint_file.seek(0)
    with TemporaryDirectory() as temporary:
        checkpoint = Path(temporary) / "best_v2_convnext_retrained.keras"
        with checkpoint.open("wb") as target:
            shutil.copyfileobj(checkpoint_file, target, length=MIB)

        from app.core.config import Settings
        from app.core.safety_gate import SafetyFilter
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
    gc.collect()
    return model, settings, safety, processor


def run_benchmark(checkpoint_file, image_zip, update_progress, get_resources, update_report):
    from io import BytesIO

    from PIL import Image

    checkpoint_file.seek(0)
    digest = hashlib.file_digest(checkpoint_file, "sha256").hexdigest()
    if digest != CHECKPOINT_SHA256:
        raise ValueError("Hãy chọn đúng checkpoint dự đoán 119 MB của dự án.")
    checkpoint_file.seek(0)
    image_zip.seek(0)
    with ZipFile(image_zip) as archive:
        entries = [entry for entry in archive.infolist() if not entry.is_dir()]
        mime_types = [mimetypes.guess_type(entry.filename)[0] for entry in entries]
        if len(entries) != IMAGE_COUNT or any(
            not 0 < entry.file_size <= 8 * MIB or mime not in {"image/jpeg", "image/png", "image/webp"}
            for entry, mime in zip(entries, mime_types, strict=True)
        ):
            raise ValueError("ZIP cần chứa đúng 20 ảnh JPG, PNG hoặc WebP, tối đa 8 MiB mỗi ảnh.")

        report = {
            "groups": [],
            "snapshots": [report_snapshot("Trước khi lấy mô hình dùng chung")],
            "completed": 0,
            "finished": False,
        }
        update_report(report)
        started = perf_counter()
        with track_memory() as memory:
            model, settings, safety, processor = get_resources(digest, checkpoint_file)
            from app.ml.inference import classify_batch

        report["groups"].append(report_group("Lấy mô hình dùng chung", perf_counter() - started, memory, 0))
        report["snapshots"].append(report_snapshot("Sau khi lấy mô hình dùng chung"))
        update_report(report)

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
                    del image, result, overlay, decoded
                    report["completed"] = index + 1
                    update_progress(index + 1)
            gc.collect()
            report["groups"].append(report_group(f"Lượt {start // GROUP_SIZE + 1}", perf_counter() - started, memory, len(group)))
            report["snapshots"].append(report_snapshot(f"Sau lượt {start // GROUP_SIZE + 1}"))
            update_report(report)

        # Keep the model resident while observing normal post-inference memory.
        idle_started = perf_counter()
        for elapsed in IDLE_SECONDS:
            sleep(max(0, elapsed - (perf_counter() - idle_started)))
            update_progress(IMAGE_COUNT, f"Đã xong 20 ảnh, đang đo RAM sau xử lý ({elapsed}/30 giây)")
            report["snapshots"].append(report_snapshot(f"Nghỉ {elapsed} giây, còn giữ mô hình"))
            update_report(report)
        report["finished"] = True
        return report


def main():
    import streamlit as st

    st.set_page_config(page_title="Đo RAM Streamlit", layout="wide")
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
    st.caption("RAM toàn container bao gồm tiến trình Python và bộ nhớ đệm của Linux.")
    st.table([report_snapshot("Hiện tại")])
    st.caption(
        "Python RSS là bộ nhớ vật lý của tiến trình chạy app. Cache tệp và anonymous là số liệu "
        "của toàn container. Các cột có phần giao nhau, không cộng chúng lại. "
        "Cache inactive không phải cam kết lượng RAM có thể cấp phát. "
        "OOM kill là số tiến trình đã bị hệ điều hành dừng vì thiếu bộ nhớ."
    )

    st.header("Kiểm thử 20 ảnh")
    st.caption("Sau khi xử lý đủ 20 ảnh, app tự theo dõi RAM thêm 30 giây khi vẫn giữ mô hình.")
    st.caption("Mô hình được nạp một lần và dùng chung cho các lần chạy. Mỗi ảnh được giải phóng sau xử lý.")
    checkpoint_file = st.file_uploader("Checkpoint dự đoán", type="keras")
    image_zip = st.file_uploader("ZIP gồm 20 ảnh mẫu", type="zip")

    @st.cache_resource
    def benchmark_lock():
        return Lock()

    @st.cache_resource(show_spinner=False, max_entries=1)
    def cached_resources(checkpoint_sha256, _checkpoint_file):
        return load_benchmark_resources(_checkpoint_file)

    run_requested = st.button("Chạy 5 lượt", disabled=checkpoint_file is None or image_zip is None)
    groups_placeholder = st.empty()
    snapshots_placeholder = st.empty()

    def publish_report(report):
        st.session_state.benchmark_memory_report = report
        with groups_placeholder.container():
            st.subheader("Thời gian và RAM đỉnh")
            st.table(report["groups"])
        with snapshots_placeholder.container():
            st.subheader("Bộ nhớ tại từng mốc")
            st.table(report["snapshots"])
        print("STREAMLIT_MEMORY " + json.dumps(report, ensure_ascii=False), flush=True)

    if run_requested:
        lock = benchmark_lock()
        if not lock.acquire(blocking=False):
            st.warning("Đang có một lượt kiểm thử chạy.")
        else:
            progress = st.progress(0, text="Đang nạp mô hình")
            st.session_state.pop("benchmark_memory_report", None)
            try:
                st.session_state.benchmark_memory_report = run_benchmark(
                    checkpoint_file,
                    image_zip,
                    lambda done, text=None: progress.progress(
                        done / IMAGE_COUNT, text=text or f"Đã kiểm tra {done}/{IMAGE_COUNT} ảnh",
                    ),
                    cached_resources,
                    publish_report,
                )
            except (BadZipFile, OSError, RuntimeError, ValueError) as error:
                st.error(str(error))
            finally:
                lock.release()

    if report := st.session_state.get("benchmark_memory_report"):
        if report.get("finished"):
            st.success("20/20 ảnh có cả Grad-CAM và Spatial Energy.")
        else:
            st.info(f"Đã xác nhận {report.get('completed', 0)}/20 ảnh. Bảng bên trên là số liệu đã thu được.")
        publish_report(report)
        st.caption(
            "Số đo được lấy khoảng mỗi 0,1 giây. Ba dòng cuối ghi nhận sau xử lý khi mô hình "
            "vẫn ở trong RAM. Một lượt thử cho thấy xu hướng trong lượt đó, chưa kết luận được rò rỉ bộ nhớ."
        )


if __name__ == "__main__":
    main()
