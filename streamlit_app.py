from pathlib import Path


CGROUP_ROOT = Path("/sys/fs/cgroup")
UNLIMITED = 1 << 60


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
        column.metric(label, f"{value / 1024**3:.2f} GiB")
    st.caption("Ứng dụng chỉ đọc số liệu bộ nhớ của container Linux.")


if __name__ == "__main__":
    main()
