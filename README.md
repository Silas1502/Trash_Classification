# Khóa Luận Tốt Nghiệp: Phân Loại Rác Thải Bằng Deep Learning (Trash Classification)

Dự án nghiên cứu và xây dựng hệ thống phân loại rác thải tự động dựa trên thị giác máy tính và học sâu (Deep Learning), ứng dụng kiến trúc **Hierarchical ConvNeXt-Tiny** kết hợp kỹ thuật huấn luyện hai giai đoạn (Two-Stage Training) và suy luận đa góc nhìn (5-View TTA).

* **Sinh viên thực hiện:** Võ Minh Khôi & Phan Trần Phúc
* **Tài liệu tham khảo chi tiết:** [docs/Luong_hoat_dong.md](docs/Luong_hoat_dong.md) và [docs/KLTN_VoMinhKhoi_PhanTranPhuc.docx](docs/KLTN_VoMinhKhoi_PhanTranPhuc.docx)

---

## 🌟 Điểm nổi bật về kiến trúc & kỹ thuật

1. **Kiến trúc phân cấp siêu lớp (Hierarchical Multi-task):**
   * **Sub-class Head (4 lớp con):** `glass`, `metal`, `paper`, `plastic` sử dụng chuẩn hóa L2 và tầng góc `CosineDense(scale=20.0)`.
   * **Super-class Head (3 siêu lớp):** `cellulose`, `metal`, `polymer_glass`.
   * **Trích xuất đặc trưng:** Backbone ConvNeXt-Tiny kết hợp song song Global Average Pooling (GAP) và Global Max Pooling (GMP).
2. **Chiến lược tăng cường dữ liệu nâng cao:**
   * Tăng cường hình học (xoay, lật, co giãn) kết hợp ngẫu nhiên **Mixup & CutMix** ($\alpha = 0.2$).
3. **Chiến lược huấn luyện 2 giai đoạn (Two-Stage Training):**
   * **Giai đoạn 1 (Warm-up Heads - 15 Epochs):** Đóng băng backbone, huấn luyện các Head phân loại với AdamW ($lr = 3\times 10^{-4}$).
   * **Giai đoạn 2 (Deep Fine-Tuning - 25 Epochs):** Mở khóa 40 layers đỉnh backbone, tối ưu với CosineDecay ($lr_{start} = 10^{-4}$).
4. **Suy luận kiểm thử đa góc nhìn (5-View TTA Inference):**
   * Tạo 5 biến thể hình học cho mỗi ảnh test (Gốc, Lật ngang, Xoay $90^\circ$, Xoay $270^\circ$, Cắt tâm 90%) và tổng hợp xác suất Softmax Ensemble.
5. **Mô hình đối sánh (Benchmarks):**
   * Đối sánh toàn diện với **ResNet50**, **ResNet50v2** và **EfficientNetV2-S**.

---

## 📁 Cấu trúc thư mục dự án

```text
.
├── checkpoints/               # Trọng số mô hình đã huấn luyện (.keras, .h5)
│   ├── convnext_tiny/
│   ├── resnet50/
│   └── resnet50v2/
│
├── data/                      # Dữ liệu hình ảnh và tập nén (không push lên git)
│   ├── datasets/              # Các biến thể tập dữ liệu (TrashNet, MyTrashNet...)
│   ├── splits/                # File phân chia dữ liệu kiểm thử (test_set_chuan_10_percent.csv)
│   └── zips/                  # Lưu trữ các file nén dữ liệu (.zip)
│
├── docs/                      # Tài liệu đồ án và mô tả luồng hoạt động
│   ├── KLTN_VoMinhKhoi_PhanTranPhuc.docx
│   └── Luong_hoat_dong.md
│
├── notebooks/                 # Jupyter Notebooks nghiên cứu và thực nghiệm
│   ├── convnext/              # Huấn luyện và đánh giá ConvNeXt (Tiny/Base)
│   ├── efficientnet/          # Huấn luyện và đánh giá EfficientNetV2-S
│   ├── resnet/                # Huấn luyện và đánh giá ResNet50 & ResNet50v2
│   └── data_preparation/      # Tiền xử lý, lọc trùng lặp dữ liệu ảnh
│
├── reports/                   # Báo cáo kết quả, phân tích lỗi, lịch sử huấn luyện
│   ├── duplicates_report.csv
│   ├── danh_sach_sai_baseline_test.csv
│   └── stage2_history.json
│
├── src/                       # Module mã nguồn Python dùng chung
│   └── __init__.py
│
├── .gitignore                 # Chặn file nặng (data, weights) khi push lên GitHub
├── README.md                  # Tài liệu giới thiệu dự án
└── requirements.txt           # Danh sách các thư viện phụ thuộc
```

---

## 🚀 Hướng dẫn cài đặt & chạy thử

### 1. Cài đặt môi trường
Khuyến nghị sử dụng Python 3.10 trở lên:

```bash
# Tạo môi trường ảo
python -m venv .venv

# Kích hoạt môi trường (Windows PowerShell)
& .venv\Scripts\Activate.ps1

# Cài đặt các thư viện cần thiết
pip install -r requirements.txt
```

### 2. Chạy thử nghiệm
* Khởi động Jupyter Notebook hoặc JupyterLab:
  ```bash
  jupyter notebook
  ```
* Truy cập thư mục `notebooks/` và chọn luồng thực nghiệm:
  * **Xử lý dữ liệu:** `notebooks/data_preparation/preparation_data.ipynb`
  * **Mô hình chính (ConvNeXt-Tiny):** `notebooks/convnext/kltn-convnext-tiny.ipynb`
  * **Đánh giá & Suy luận TTA:** `notebooks/convnext/mytrashnet_convnext_retrain_tta.ipynb`

