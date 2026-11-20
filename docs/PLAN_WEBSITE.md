# 📋 KẾ HOẠCH XÂY DỰNG HỆ THỐNG FULLSTACK WEB PHÂN LOẠI RÁC THẢI (TRASH CLASSIFICATION APP)

> **Dự án:** Ứng dụng web phân loại rác thải bằng ConvNeXt-Tiny, hai chốt an toàn, XAI và lưu trữ đám mây (Supabase + ImageKit).\
> **Phạm vi:** Yêu cầu, cấu hình chạy và tiêu chí nghiệm thu của website.\
> **Giao diện tham chiếu:** Thư mục [Giao diện](../Giao%20diện)

---

## 📑 Mục lục
1. [Tổng quan đề bài & Mục tiêu](#1-tổng-quan-đề-bài--mục-tiêu)
2. [Yêu cầu kỹ thuật bắt buộc](#2-yêu-cầu-kỹ-thuật-bắt-buộc)
3. [Yêu cầu chức năng chi tiết](#3-yêu-cầu-chức-năng-chi-tiết)
   - [3.1. Cấu trúc thư mục dự án](#31-cấu-trúc-thư-mục-dự-án)
   - [3.2. Yêu cầu Backend API](#32-yêu-cầu-backend-api)
   - [3.3. Yêu cầu Database & Cloud Storage](#33-yêu-cầu-database--cloud-storage)
   - [3.4. Yêu cầu Frontend](#34-yêu-cầu-frontend)
   - [3.5. Yêu cầu Triển khai (Deployment)](#35-yêu-cầu-triển-khai-deployment)
4. [Sản phẩm nộp bài (Mô hình Monorepo)](#4-sản-phẩm-nộp-bài-mô-hình-monorepo)
5. [Tiêu chí chấm điểm & Nghiệm thu (100 Điểm)](#5-tiêu-chí-chấm-điểm--nghiệm-thu-100-điểm)
6. [Lộ trình thực hiện & Phân chia công việc](#6-lộ-trình-thực-hiện--phân-chia-công-việc)
7. [Hướng dẫn chi tiết: Tạo Project, lấy Key/Link và kết nối Fullstack (FE - BE - DB & Cloud Storage)](#7-hướng-dẫn-chi-tiết-tạo-project-lấy-keylink-và-kết-nối-fullstack-fe---be---db--cloud-storage)
   - [7.1. Cấu hình Supabase & Lấy SUPABASE_URL + SUPABASE_KEY (Kèm SQL tạo bảng)](#71-cấu-hình-supabase--lấy-supabase_url--supabase_key-kèm-sql-tạo-bảng)
   - [7.2. Cấu hình ImageKit.io & Lấy API Credentials (IMAGEKIT_PUBLIC_KEY, PRIVATE_KEY, URL_ENDPOINT)](#72-cấu-hình-imagekitio--lấy-api-credentials-imagekit_public_key-private_key-url_endpoint)
   - [7.3. Cấu hình triển khai Backend FastAPI trên Render (từ Monorepo)](#73-cấu-hình-triển-khai-backend-fastapi-trên-render-từ-monorepo)
   - [7.4. Cấu hình triển khai Frontend Next.js trên Vercel (từ Monorepo)](#74-cấu-hình-triển-khai-frontend-nextjs-trên-vercel-từ-monorepo)
   - [7.5. Hoàn tất kết nối Fullstack khép kín (Handshake & CORS)](#75-hoàn-tất-kết-nối-fullstack-khép-kín-handshake--cors)
   - [7.6. Chiến lược UptimeRobot kép (đã bật monitor Render)](#76-chiến-lược-uptimerobot-kép)

---

## 1. Tổng quan đề bài & Mục tiêu

### Mô tả dự án
Xây dựng một ứng dụng web **Fullstack** hoàn chỉnh cho bài toán **Phân loại rác thải tự động (Trash Classification App)** ứng dụng Thị giác máy tính và Học sâu (Deep Learning). Hệ thống cho phép người dùng tải lên 1 ảnh đơn lẻ hoặc xử lý hàng loạt theo thư mục ảnh. 

Hệ thống dùng mô hình học sâu và hai chốt cơ sở để phân luồng kết quả.
- **Loại rác:** Nhựa, Giấy, Kim loại hoặc Thủy tinh theo checkpoint hiện tại.
- **Chốt 1 – Độ tin cậy:** Xác suất cao nhất của mô hình, so với ngưỡng riêng của lớp dự đoán.
- **Chốt 2 – Biên khoảng cách:** Chênh lệch xác suất giữa hai lớp đứng đầu, so với ngưỡng chung.
- **Luồng xử lý:** Cả hai chốt đạt → `Tự động` (`Tu_Dong_Gap`), trạng thái `Thành công`. Một trong hai chốt chưa đạt → `Thủ công` (`Chuyen_Khay_Thu_Cong`), trạng thái `Cần kiểm tra`.
- **Hiển thị:** Mỗi chốt có định dạng `giá trị % (ngưỡng %)` cùng kết quả đạt hoặc chưa đạt trong phần chi tiết.
- **Trí tuệ nhân tạo có thể giải thích (Explainable AI - XAI):** Tích hợp kỹ thuật **Grad-CAM (Gradient-weighted Class Activation Mapping)** và **Spatial Activation Energy Map** để trực quan hóa bản đồ nhiệt (Heatmap Overlay), minh bạch hóa lý do mô hình đưa ra dự đoán phân loại.

Ảnh gốc, Grad-CAM và Spatial Energy được lưu trên **ImageKit**. Kết quả phân loại và URL ảnh được lưu trong **Supabase PostgreSQL**.

### Mục tiêu đạt được
- Đóng gói mô hình **ConvNeXt-Tiny ONNX FP32** để suy luận trên Render.
- Xây dựng RESTful API backend bất đồng bộ hiệu năng cao bằng **FastAPI**.
- Xây dựng giao diện frontend hiện đại, chuẩn xác theo thiết kế bằng **Next.js 16 (App Router)** và **Tailwind CSS**.
- Tích hợp **ImageKit** để lưu và phân phối ảnh gốc cùng hai ảnh XAI.
- Dùng **Supabase PostgreSQL** cho lịch sử, tìm kiếm, phân trang và xuất CSV.
- Theo dõi trạng thái bằng health check trong giao diện và monitor UptimeRobot cho backend Render.
- Nắm vững toàn bộ quy trình phát triển và triển khai sản phẩm phần mềm AI end-to-end.

---

## 2. Yêu cầu kỹ thuật bắt buộc

### 2.1. Tech Stack quy định

| Layer | Công nghệ | Dịch vụ / Hosting | Mô tả chức năng |
|:---|:---|:---|:---|
| **ML Model** | ConvNeXt-Tiny; TensorFlow/Keras để huấn luyện và xuất mô hình, ONNX Runtime FP32 để phục vụ dự đoán | `backend/model-parts/` | Suy luận 5-view TTA, hai chốt, Grad-CAM và Spatial Energy |
| **Backend** | FastAPI, Native Python 3.12 | Render Free | REST API, tiền xử lý, suy luận và điều phối lưu trữ |
| **Frontend** | Next.js 16 (React) + TypeScript + Tailwind CSS | Vercel | Giao diện người dùng responsive, kéo thả ảnh/thư mục, hiển thị kết quả |
| **Cloud Storage** | ImageKit; có adapter Supabase Storage dự phòng | ImageKit | Lưu ảnh gốc và hai ảnh XAI. Gói Free công bố 3 GB lưu trữ và 20 GB băng thông/tháng. [Bảng giá](https://imagekit.io/plans) |
| **Database** | Supabase (PostgreSQL) | Supabase Cloud | Lưu bảng lịch sử `prediction_logs` |
| **Giám sát** | `/api/v1/health`, đèn trạng thái và monitor HTTP cho Render | FastAPI / Next.js / UptimeRobot | UptimeRobot kiểm tra HTTP. Frontend đọc JSON để hiển thị trạng thái mô hình và dịch vụ phụ thuộc. |
| **Repository** | Monorepo (1 Repo duy nhất) | GitHub | Quản lý chung cả frontend/ và backend/, kết nối độc lập với Render (Root: backend) và Vercel (Root: frontend) |
| **Version Control**| Git + GitHub | GitHub | Quản lý phiên bản mã nguồn dự án |

### 2.2. Kiến trúc luồng dữ liệu bắt buộc

```
┌────────────────────────┐      ┌─────────────────────────┐      ┌────────────────────────┐
│   Frontend (Next.js)   │────▶│    FastAPI Backend      │────▶│     ImageKit Storage   │
│  - Tab 1 ảnh           │◀────│  - Image Preprocess     │◀────│   (Ảnh gốc, Grad-CAM   │
│  - Tab nhiều ảnh       │      │  - ONNX Inference       │      │    và Spatial Energy)   │
│  - Trang Lịch sử       │      │  - Two-Gate Safety Core │      └────────────────────────┘
└────────────────────────┘      └─────────────────────────┘                  │
         ▲                                   │                               │ URL ảnh
         │                                   │                               ▼
         │                                   │                   ┌────────────────────────┐
         │                                   └──────────────────▶│   Supabase Database    │
         └───────────────────────────────────────────────────────│      (PostgreSQL)      │
                       Hiển thị dữ liệu & Ảnh CDN                │ (Lưu log kết quả phân) │
                                                                 └────────────────────────┘
```

---

## 3. Yêu cầu chức năng chi tiết

### 3.1. Cấu trúc thư mục dự án

```text
TRASH_CLASSIFICATION_SYSTEM/
├── 📂 backend/                                # [B1-B12] Source code FastAPI Backend
│   ├── 📂 app/
│   │   ├── 📂 api/
│   │   │   ├── 📂 endpoints/
│   │   │   │   ├── predict.py                # API /predict/single, /predict/batch
│   │   │   │   ├── history.py                # API /history, /history/{id}, /history/export, /history/statistics
│   │   │   │   └── system.py                 # API /health, /model-info
│   │   │   └── router.py                     # Tiền tố /api/v1
│   │   ├── 📂 core/
│   │   │   ├── config.py                     # Quản lý cấu hình & biến môi trường (.env)
│   │   │   ├── safety_thresholds.json        # File JSON chứa toàn bộ ngưỡng an toàn trích xuất từ Notebook (Cell 13)
│   │   │   └── safety_gate.py                # Đọc ngưỡng và phân luồng theo hai chốt cơ sở
│   │   ├── 📂 db/
│   │   │   ├── supabase_db.py        # Adapter Supabase PostgreSQL (REST API & Auth key)
│   │   │   ├── imagekit_storage.py           # Upload ảnh gốc và ảnh XAI lên ImageKit
│   │   │   ├── storage.py                    # Kiểu dữ liệu dùng chung cho lưu ảnh
│   │   │   └── supabase_storage.py           # Lưu ảnh dự phòng khi thiếu cấu hình ImageKit
│   │   ├── 📂 ml/                            # Pipeline TensorFlow dùng cho chạy local
│   │   │   ├── custom_layers.py              # Định nghĩa lớp CosineDense để nạp model Keras
│   │   │   ├── model_loader.py               # Nạp weights ConvNeXt-Tiny (.keras) & sub_logits_model
│   │   │   ├── preprocessor.py               # Resize 320x320 AREA, chuẩn hóa ConvNeXt
│   │   │   ├── inference.py                  # Hàm suy luận 5-View TTA và Single-View
│   │   │   └── xai_engine.py                 # Trích xuất Grad-CAM & JET Heatmap Overlay
│   │   ├── 📂 schemas/
│   │   │   ├── prediction.py                 # Pydantic Schemas kết quả dự đoán
│   │   │   └── history.py                    # Pydantic Schemas lịch sử & bộ lọc
│   │   └── main.py                           # Khởi tạo FastAPI app, Lifespan nạp model 1 lần, CORS
│   ├── 📂 onnx_fp32/                         # Runtime, adapter, giải mã mô hình và lock thư viện
│   ├── 📂 model-parts/                       # Mô hình ONNX mã hóa và manifest SHA256
│   ├── start-render.sh                       # Giải mã mô hình rồi chạy FastAPI ONNX
│   ├── requirements.txt                     # Thư viện backend TensorFlow cho chạy local
│   └── .env.example                          # Mẫu cấu hình môi trường
│
├── 📂 frontend/                               # [F1-F10] Source code Next.js 16
│   ├── 📂 src/
│   │   ├── 📂 app/                           # App Router (Pages & Layouts)
│   │   │   ├── layout.tsx                    # Root layout chứa Sidebar cố định
│   │   │   ├── page.tsx                      # Landing / Redirect sang /classify
│   │   │   ├── 📂 classify/                  
│   │   │   │   └── page.tsx                  # Trang Phân loại (Tab Một ảnh & Tab Nhiều ảnh)
│   │   │   └── 📂 history/                   
│   │   │       └── page.tsx                  # Trang Lịch sử (Bảng và cửa sổ chi tiết)
│   │   ├── 📂 components/                    # UI Components
│   │   │   ├── 📂 layout/
│   │   │   │   └── Sidebar.tsx               # Sidebar màu xanh navy đậm cố định
│   │   │   ├── 📂 classify/
│   │   │   │   ├── SingleImageUpload.tsx     # Khối kéo thả 1 ảnh + Xem trước (Preview)
│   │   │   │   ├── SingleImageResult.tsx     # Hiển thị Loại rác, hai chốt có ngưỡng, gợi ý
│   │   │   │   ├── BatchImageUpload.tsx      # Kéo thả nhiều ảnh hoặc chọn thư mục
│   │   │   │   ├── BatchProgressBar.tsx      # 4 thẻ thống kê, cập nhật sau mỗi lô
│   │   │   │   └── BatchResultTable.tsx      # Bảng kết quả danh sách ảnh đã xử lý
│   │   │   ├── 📂 history/
│   │   │   │   ├── HistoryFilterBar.tsx      # Bộ lọc tìm kiếm, loại rác, luồng, thời gian
│   │   │   │   ├── HistoryTable.tsx          # Bảng danh sách lịch sử có phân trang
│   │   │   │   └── PredictionDetails.tsx     # Nội dung cửa sổ chi tiết dự đoán
│   │   │   └── 📂 ui/                        # Button, Badge, ProgressBar, Input, Modal...
│   │   ├── 📂 services/                      # Giao tiếp HTTP API
│   │   │   ├── api.ts                        # Cấu hình Axios client
│   │   │   ├── predictService.ts             # Gọi API dự đoán 1 ảnh / nhiều ảnh
│   │   │   └── historyService.ts             # Gọi API lịch sử, chi tiết và xuất CSV
│   │   ├── 📂 types/                         # TypeScript Definitions
│   │   │   └── index.ts                      # Interface cho PredictResult, HistoryItem...
│   │   └── 📂 lib/                           # Utility functions
│   ├── .env.example                          # Biến môi trường (NEXT_PUBLIC_API_URL)
│   ├── package.json                          # Dependencies & Scripts
│   └── tailwind.config.ts                    # Cấu hình giao diện Tailwind
│
├── 📂 docs/                                  # Tài liệu dự án
│   ├── Luong_hoat_dong.md                    # Tài liệu luồng Deep Learning ConvNeXt-Tiny
│   └── PLAN_WEBSITE.md                       # Bản kế hoạch này
│
├── 📂 Giao diện/                             # Chứa 4 ảnh giao diện tham chiếu
│   ├── Phân loại 1 ảnh.png
│   ├── Phân loại thư mục nhiều ảnh.png
│   ├── Lịch sử trước khi chọn 1 dòng.png
│   └── Lịch sử hiển thị thông tin chi tiết 1 dòng.png
│
├── .gitignore                                # Chặn upload checkpoints nặng, .env, node_modules
└── README.md                                 # Hướng dẫn cài đặt & vận hành hệ thống
```

---

### 3.2. Yêu cầu Backend API

Các endpoint nghiệp vụ trong bảng dùng tiền tố `/api/v1`.

| # | Yêu cầu | Chi tiết kỹ thuật | Mức độ |
|---|---|---|---|
| **B1** | Tạo FastAPI App & Swagger UI | Khởi tạo ứng dụng FastAPI với tài liệu API tự động tại `/docs` (Swagger UI) và `/redoc`. | Bắt buộc |
| **B2** | Health Check (`GET /health`) | `/api/v1/health` trả trạng thái đã lưu của mô hình, Supabase và ImageKit. `HEAD` dùng để kiểm tra kết nối; đọc trường `status` trong JSON để phân biệt `healthy` và `degraded`. | Bắt buộc |
| **B3** | Phân loại 1 ảnh (`POST /predict/single`) | Nhận trường multipart `file`, giải mã RGB bằng Pillow, cắt vuông giữa ảnh, resize AREA về 320×320 và suy luận ONNX. Bản Render dùng 5-view TTA rồi áp dụng hai chốt và tạo Grad-CAM, Spatial Energy. Backend upload ba ảnh lên ImageKit, ghi Supabase và trả kết quả. | Bắt buộc |
| **B4** | Phân loại nhiều ảnh / thư mục (`POST /predict/batch`) | API nhận các trường multipart `files`. Giao diện gửi tuần tự từng lô tối đa 4 ảnh và 32 MiB. Render xử lý, lưu và giải phóng bộ đệm từng ảnh trước ảnh tiếp theo. Phản hồi gồm thống kê, `results` và `errors` theo chỉ số ảnh. | Bắt buộc |
| **B5** | Phân luồng theo hai chốt cơ sở | Backend đọc ngưỡng độ tin cậy theo lớp và ngưỡng biên khoảng cách chung từ `safety_thresholds.json`.<br/>- **Tự động:** Độ tin cậy và biên khoảng cách đều đạt ngưỡng tương ứng.<br/>- **Thủ công:** Ít nhất một chốt chưa đạt. Trường `reason` ghi rõ chốt nào chưa đạt.<br/>- API trả giá trị đo (`confidence`, `margin`), hai ngưỡng (`checkpoint_1`, `checkpoint_2`) và cờ đạt ngưỡng tương ứng. | Bắt buộc |
| **B6** | Input Validation bằng Pydantic | API kiểm tra kiểu request, MIME, dữ liệu ảnh, giới hạn 8 MiB và 16 MP mỗi ảnh. `413` báo vượt kích thước upload, `415` báo loại tệp không hỗ trợ; `400` hoặc `422` áp dụng cho các trường hợp dữ liệu lỗi tương ứng. | Bắt buộc |
| **B7** | Lấy danh sách lịch sử (`GET /history`) | Supabase hỗ trợ phân trang (`page`, `limit`), sắp xếp `created_at` giảm dần, lọc loại rác, luồng, khoảng thời gian và tìm tên file. | Bắt buộc |
| **B8** | Chi tiết 1 bản ghi lịch sử (`GET /history/{id}`) | Đọc bản ghi theo `id`, gồm URL ảnh ImageKit, chỉ số dự đoán và metadata. | Bắt buộc |
| **B9** | Xuất dữ liệu lịch sử (`GET /history/export`) | Xuất CSV theo bộ lọc. Code đặt trần truy vấn 5.000 bản ghi mỗi lượt xuất. | Nâng cao |
| **B10**| CORS Middleware & Error Handling | Cấu hình middleware CORS cho phép frontend Next.js gọi API; cơ chế bắt lỗi tập trung (Global Exception Handler) chuẩn hóa format lỗi JSON. | Bắt buộc |
| **B11**| Thông tin Model (`GET /model-info`) | Trả về thông tin kiến trúc mô hình (ConvNeXt-Tiny), phiên bản checkpoint, kích thước ảnh đầu vào ($320 \times 320$) và toàn bộ nội dung cấu hình bộ ngưỡng an toàn đọc trực tiếp từ file `safety_thresholds.json`. Trường `adaptive_assessment_enabled` có giá trị `false` ở cấu hình hiện tại. | Bonus |
| **B12** | Giải thích mô hình với XAI | Trích đặc trưng từ `convnext_tiny_stage_3_block_2_identity`, tính Grad-CAM bằng đồ thị gradient ONNX và Spatial Energy từ kích hoạt. Hai ảnh phủ nhiệt dùng bảng màu JET, được lưu trên ImageKit. | Nâng cao |
| **B13** | Thống kê lịch sử (`GET /history/statistics`) | Nhận `start_date` và `end_date` theo dạng `YYYY-MM-DD`. Tính cả hai ngày theo giờ Việt Nam. Supabase đếm chính xác toàn bộ bản ghi trong khoảng, theo loại rác và theo luồng xử lý. | Nâng cao |
| **B14** | Dữ liệu biểu đồ lịch sử (`GET /history/trends`) | Nhận `period=today\|week\|month\|quarter`. Hôm nay bắt đầu lúc 00:00 theo giờ Việt Nam, trả 24 mốc giờ với cờ `is_future` cho các giờ chưa tới. Các khoảng còn lại dùng 7, 30, 90 ngày gần nhất. Trả tổng số ảnh và số ảnh theo luồng ở từng mốc, cùng tổng theo loại rác trong cả khoảng. | Nâng cao |
| **B15** | Số liệu theo ngày (`GET /history/daily`) | Nhận `start_date`, `end_date` và `page`. Mỗi trang trả tối đa 5 ngày, có tổng số ngày và tổng số trang. Khoảng ngày tính cả hai đầu theo giờ Việt Nam. Chỉ truy vấn các ngày thuộc trang đang xem. | Nâng cao |

#### Chi tiết Quy trình Xử lý Dữ liệu trước khi nạp vào Mô hình
Bản chạy trên Render dùng pipeline ONNX chuyển từ mô hình ConvNeXt-Tiny của notebook `kltn-convnext-tiny.ipynb`.

```
┌─────────────────┐      ┌─────────────────────────┐      ┌─────────────────────────┐
│  Raw Image File │────▶│ 1. Giải mã & chuẩn màu   │────▶│ 2. Cắt vuông giữa ảnh   │
│  (UploadFile)   │      │    (Pillow → RGB)        │      │    (Center crop)        │
└─────────────────┘      └─────────────────────────┘      └─────────────────────────┘
                                                                       │
┌─────────────────────────┐      ┌─────────────────────────┐           │
│ 5. ONNX 5-View TTA    │◀────│ 4. RGB float32           │◀──────────┘
│   & Đánh giá 2 Chốt    │      │ (Đầu vào đồ thị ONNX)    │      3. Area Resampling
│ (Softmax + Tau1 + Tau2)│      │                          │       (320×320)
└─────────────────────────┘      └─────────────────────────┘
```

1. **Bước 1: Tiếp nhận và giải mã hình ảnh (Image Decoding):**
   - Đọc dữ liệu nhị phân (bytes) từ request tải lên.
   - Pillow kiểm tra dữ liệu, xử lý chiều xoay EXIF và chuyển sang RGB ba kênh.
2. **Bước 2: Cắt vuông giữa ảnh (Center Square):**
   - Bản Render dùng `smart_crop=false`.
   - Theo kích thước ảnh RGB, chọn cạnh hình vuông $a = \min(h, w)$.
   - Tọa độ góc trái vùng cắt là $(\lfloor(w-a)/2\rfloor, \lfloor(h-a)/2\rfloor)$.
3. **Bước 3: Tái định cỡ quang học chống răng cưa (Optical Area Resampling):**
   - Định cỡ lại ảnh vuông đã cắt về kích thước chuẩn của mô hình: $\text{IMG\_SIZE} = (320, 320)$.
   - Runtime ONNX dùng phép lấy mẫu vùng tương thích với ResizeArea của TensorFlow.
4. **Bước 4: Chuẩn bị đầu vào ONNX:**
   - Chuyển ảnh về mảng RGB `float32` kích thước 320×320×3.
   - Đưa mảng RGB vào đồ thị được xuất từ mô hình ConvNeXt-Tiny.
5. **Bước 5: Suy luận Đa góc nhìn (5-View TTA Inference) & Tổng hợp Softmax:**
   - Theo Cell 9 của notebook, để tăng cường độ ổn định và giảm thiểu phương sai dự đoán, hệ thống sinh ra 5 biến thể hình học cho ảnh:
     * *View 1:* Ảnh RGB 320×320 sau tiền xử lý.
     * *View 2:* Lật ngang (`flip_left_right`).
     * *View 3:* Xoay $90^\circ$ ngược chiều kim đồng hồ (`rot90, k=1`).
     * *View 4:* Xoay $270^\circ$ ngược chiều kim đồng hồ (`rot90, k=3`).
     * *View 5:* Cắt giữa, giữ 90% chiều rộng và chiều cao, rồi resize AREA về $320 \times 320$.
   - Trích xuất Logits từ tầng `CosineDense(scale=20.0)` và tính xác suất Softmax cho từng View: $P^{(v)} = \text{softmax}(\text{logits}^{(v)})$.
   - Lấy trung bình xác suất: $P = \frac{1}{5}\sum_{v=1}^5 P^{(v)}$. Backend hỗ trợ cấu hình một góc nhìn; bản Render hiện dùng năm.
6. **Bước 6: Phân luồng theo hai chốt cơ sở:**
   - Backend nạp ngưỡng độ tin cậy riêng theo lớp ($\tau_{conf}(c)$) và ngưỡng biên khoảng cách chung ($\tau_{margin}$) từ `safety_thresholds.json` khi khởi động.
   - **Chốt độ tin cậy:** $Conf = \max_c P(c)$. Chốt đạt khi $Conf \ge \tau_{conf}(c)$ với $c$ là lớp dự đoán.
   - **Chốt biên khoảng cách:** $Margin = P_{Top1} - P_{Top2}$. Chốt đạt khi $Margin \ge \tau_{margin}$.
   - **Tự động:** Cả hai chốt đạt. Backend trả `Tu_Dong_Gap` và `Thành công`.
   - **Thủ công:** Một hoặc cả hai chốt chưa đạt. Backend trả `Chuyen_Khay_Thu_Cong` và `Cần kiểm tra`, kèm lý do của từng chốt chưa đạt.
   - Kết quả mô phỏng luôn được đánh dấu `Thủ công`. Quy tắc hai chốt áp dụng cho dự đoán từ checkpoint thật.
   - Cấu hình web dùng `ADAPTIVE_ASSESSMENT_ENABLED=false` để tắt hai nhánh xét lại bằng điểm bù trừ và đồng thuận TTA. Khi bật suy luận 5 góc nhìn, TTA vẫn tính trung bình xác suất đầu vào cho hai chốt.
   - Các trường `composite_score`, `tta_stability` và `decision_tier` vẫn được lưu để đọc lịch sử và giữ định dạng API. Việc phân luồng hiện tại dựa vào kết quả của hai chốt cơ sở.
7. **Bước 7: Giải thích mô hình bằng XAI (Grad-CAM & Spatial Energy Map - Cell 12):**
   - Trích xuất ma trận đặc trưng không gian $F \in \mathbb{R}^{10 \times 10 \times C}$ từ tầng cuối trước pooling (`convnext_tiny_stage_3_block_2_identity`).
   - Tính toán bản đồ năng lượng kích hoạt: $\text{Energy}_{i,j} = \sqrt{\frac{1}{C}\sum_k (F_{i,j}^k)^2}$.
   - Đồ thị gradient ONNX tính gradient của lớp dự đoán để tạo Grad-CAM. Trọng số mỗi kênh là trung bình không gian của gradient tương ứng.
   - Phóng bản đồ nhiệt lên $320 \times 320$ bằng Bicubic, tô màu `cv2.COLORMAP_JET` và phủ lên ảnh đã tiền xử lý.
   - Lưu ảnh gốc, Grad-CAM và Spatial Energy lên ImageKit; ghi ba URL vào lịch sử Supabase.

#### Cấu trúc JSON Response của API `/api/v1/predict/single`:
```json
{
  "id": "c1f7b0a8-5d23-4e89-a6f1-3d7120a4b889",
  "file_name": "plastic_bottle_01.jpg",
  "image_url": "https://ik.imagekit.io/example-id/uploads/plastic/c1f7b0a8-5d23-4e89-a6f1-3d7120a4b889_original_plastic_bottle_01.jpg",
  "xai_overlay_url": "https://ik.imagekit.io/example-id/uploads/xai/c1f7b0a8-5d23-4e89-a6f1-3d7120a4b889_gradcam_overlay.jpg",
  "xai_energy_overlay_url": "https://ik.imagekit.io/example-id/uploads/xai/c1f7b0a8-5d23-4e89-a6f1-3d7120a4b889_spatial_energy_overlay.jpg",
  "is_mock": false,
  "waste_type": "Nhựa",
  "confidence": 90.0,
  "margin": 85.0,
  "top_predictions": [
    {"waste_type": "Nhựa", "probability": 90.0},
    {"waste_type": "Thủy tinh", "probability": 5.0}
  ],
  "processing_time_ms": 72.5,
  "checkpoint_1": 75.64,
  "checkpoint_2": 54.34,
  "confidence_gate_passed": true,
  "margin_gate_passed": true,
  "composite_score": 137.7036,
  "tta_stability": 100.0,
  "decision_tier": "Tier 1: Đạt chuẩn cơ sở",
  "decision": "Tu_Dong_Gap",
  "pipeline_type": "Tự động",
  "status": "Thành công",
  "reason": "Đạt cả hai chốt (Chốt 1: 1.19x | Chốt 2: 1.56x).",
  "suggestion": "Thu gom vào thùng rác tái chế.",
  "created_at": "2026-11-16T08:32:15.000Z"
}
```

---

### 3.3. Yêu cầu Database & Cloud Storage

| # | Yêu cầu | Chi tiết kỹ thuật | Mức độ |
|---|---|---|---|
| **D1** | Cấu hình ImageKit | Thiết lập `IMAGEKIT_PUBLIC_KEY`, `IMAGEKIT_PRIVATE_KEY` và `IMAGEKIT_URL_ENDPOINT` ở backend. Render hiện lưu ảnh bằng ImageKit. | Bắt buộc |
| **D2** | Module kết nối Cloud Storage (`imagekit_storage.py`) | Với cả hai chế độ dự đoán, backend lưu ảnh gốc trực tiếp trong `uploads/plastic/`, `uploads/paper/`, `uploads/metal/`, `uploads/glass/` hoặc `uploads/manual/`. Hai ảnh giải thích được lưu riêng trong `uploads/xai/`. Tên tệp có mã dự đoán để tránh trùng và giữ liên kết với lịch sử. Có adapter Supabase Storage dự phòng khi đã cấu hình Supabase và thiếu cấu hình ImageKit. | Bắt buộc |
| **D3** | Cấu hình Supabase PostgreSQL | Dùng bảng `prediction_logs` để đọc, lọc, ghi và xuất kết quả. Biến kết nối được đặt ở backend. | Bắt buộc |
| **D4** | Thiết kế bảng `prediction_logs` | Lưu kết quả phân loại, hai chốt, quyết định, thời gian, metadata, `is_mock`, `image_url`, `xai_overlay_url` và `xai_energy_overlay_url`. Bản ghi mới lưu hai lớp đứng đầu trong `metadata.top_predictions`. | Bắt buộc |
| **D5** | Thống kê phiên xử lý nhiều ảnh | API trả `batch_id`, `total_images`, `processed_images`, `pending_images`, `succeeded_images`, `failed_images`, `completion_rate`, `results` và `errors`. Supabase lưu lịch sử theo từng ảnh. | Nâng cao |
| **D6** | Chỉ mục trên cơ sở dữ liệu | SQL thiết lập tạo chỉ mục cho `created_at`, `waste_type` và `pipeline_type`. Tìm tên tệp bằng `ILIKE` trong adapter Supabase. | Bắt buộc |
| **D7** | Xử lý lỗi dịch vụ phụ thuộc | Backend kiểm tra Supabase và ImageKit theo chu kỳ. Khi lưu trữ hoặc database lỗi, API trả lỗi tương ứng; batch có thể trả kết quả một phần kèm lỗi theo ảnh. | Nâng cao |
| **D8** | Xóa ảnh theo lịch sử Supabase | Đã cài SQL trigger/hàng đợi trên Supabase và triển khai tác vụ dọn ImageKit trên Render. Khi backend chạy, kiểm tra mỗi 60 giây, xóa ảnh gốc cùng hai ảnh XAI và thử lại khi lỗi. Bản ghi cũ chỉ có URL vẫn được hỗ trợ. Xem [hướng dẫn](IMAGEKIT_CLEANUP.md). | Nâng cao |

#### Cấu trúc Bản ghi dữ liệu mẫu (`prediction_logs`):
```json
{
  "id": "c1f7b0a8-5d23-4e89-a6f1-3d7120a4b889",
  "file_name": "plastic_bottle_01.jpg",
  "image_url": "https://ik.imagekit.io/example-id/uploads/plastic/c1f7b0a8-5d23-4e89-a6f1-3d7120a4b889_original_plastic_bottle_01.jpg",
  "xai_overlay_url": "https://ik.imagekit.io/example-id/uploads/xai/c1f7b0a8-5d23-4e89-a6f1-3d7120a4b889_gradcam_overlay.jpg",
  "xai_energy_overlay_url": "https://ik.imagekit.io/example-id/uploads/xai/c1f7b0a8-5d23-4e89-a6f1-3d7120a4b889_spatial_energy_overlay.jpg",
  "is_mock": false,
  "waste_type": "Nhựa",
  "confidence": 90.0,
  "margin": 85.0,
  "checkpoint_1": 75.64,
  "checkpoint_2": 54.34,
  "confidence_gate_passed": true,
  "margin_gate_passed": true,
  "composite_score": 137.7036,
  "tta_stability": 100.0,
  "decision_tier": "Tier 1: Đạt chuẩn cơ sở",
  "decision": "Tu_Dong_Gap",
  "pipeline_type": "Tự động",
  "status": "Thành công",
  "reason": "Đạt cả hai chốt (Chốt 1: 1.19x | Chốt 2: 1.56x).",
  "suggestion": "Thu gom vào thùng rác tái chế.",
  "created_at": "2026-11-16T08:32:15.000Z",
  "metadata": {
    "file_size": 245100,
    "mime_type": "image/jpeg",
    "inference_time_ms": 38.5,
    "xai_time_ms": 12.0,
    "processing_time_ms": 72.5,
    "top_predictions": [
      {"waste_type": "Nhựa", "probability": 90.0},
      {"waste_type": "Thủy tinh", "probability": 5.0}
    ],
    "model_version": "convnext_tiny_onnx_fp32",
    "tta_views": 5,
    "crop_box": [0, 0, 320],
    "crop_strategy": "image_center"
  }
}
```

---

### 3.4. Yêu cầu Frontend

| # | Yêu cầu | Chi tiết kỹ thuật & Giao diện tham chiếu | Mức độ |
|---|---|---|---|
| **F1** | Sidebar điều hướng cố định | Bố trí thanh Sidebar nền xanh navy đậm cố định bên trái, logo thùng rác + text "Phân loại rác", menu gồm 2 mục: **Phân loại** (Icon layers) và **Lịch sử** (Icon đồng hồ). Hiển thị rõ mục đang được chọn. | Bắt buộc |
| **F2** | Màn hình Phân loại 1 ảnh (Tab "Một ảnh") | **Giao diện tham chiếu:** [Giao diện/Phân loại 1 ảnh.png](../Giao%20diện/Phân%20loại%201%20ảnh.png)<br/>- Khối bên trái: Vùng kéo thả ảnh / chọn tệp, xem trước ảnh đã chọn + tên file, nút `[▶ Bắt đầu dự đoán]` và nút `[↺ Làm mới]`.<br/>- Khối bên phải: Card Loại rác kèm badge trạng thái (`✓ Kết quả hợp lệ` hoặc `⚠ Cần kiểm tra`), luồng `Tự động`/`Thủ công` và hai thanh **Độ tin cậy** và **Biên khoảng cách** theo dạng `giá trị % (ngưỡng %)`, khung Gợi ý xử lý và **trình xem Ảnh gốc, Grad-CAM và Spatial Energy**. | Bắt buộc |
| **F3** | Màn hình Phân loại thư mục / nhiều ảnh (Tab "Nhiều ảnh") | **Giao diện tham chiếu:** [Giao diện/Phân loại thư mục nhiều ảnh.png](../Giao%20diện/Phân%20loại%20thư%20mục%20nhiều%20ảnh.png)<br/>- Khối trên trái: Kéo thả nhiều ảnh hoặc thư mục, 2 nút `[Chọn nhiều ảnh]` và `[Chọn thư mục]`.<br/>- Khối trên phải: 4 thẻ thống kê tiến độ (*Tổng số ảnh*, *Đã xử lý*, *Đang chờ*, *Tỷ lệ hoàn thành %*), thanh tiến trình cập nhật khi từng lô trả kết quả và nút `[▶ Bắt đầu xử lý]`, nút `Dừng` sau lô hiện tại.<br/>- Khối dưới: Bảng kết quả đã xử lý (Thumbnail + Tên ảnh, Loại rác, Độ tin cậy và Biên khoảng cách theo dạng `giá trị % (ngưỡng %)`, Luồng xử lý), thanh tìm kiếm tên ảnh, bộ lọc theo loại rác; hỗ trợ nhấn vào dòng để xem chi tiết. | Bắt buộc |
| **F4** | Màn hình Lịch sử phân loại (Tổng quan) | **Giao diện tham chiếu:** [Giao diện/Lịch sử trước khi chọn 1 dòng.png](../Giao%20diện/Lịch%20sử%20trước%20khi%20chọn%201%20dòng.png)<br/>- Thanh bộ lọc: Ô tìm kiếm tên file, dropdown Loại rác, dropdown Luồng xử lý (`Tất cả`/`Tự động`/`Thủ công`), dropdown Thời gian và nút `[📥 Xuất lịch sử]`.<br/>- Bảng dữ liệu: STT, Tên file, Loại rác, Độ tin cậy, Luồng xử lý (Badge màu), Thời gian dự đoán.<br/>- Phân trang: Hiển thị số lượng bản ghi và các nút chuyển trang `[<] [1] [2] ... [>]`. | Bắt buộc |
| **F5** | Cửa sổ chi tiết lịch sử | Bấm một dòng để mở cửa sổ **Chi tiết dự đoán**. Cửa sổ hiển thị ảnh gốc, Grad-CAM, Spatial Energy, tên tệp, loại rác, độ tin cậy và biên khoảng cách theo dạng `giá trị % (ngưỡng %)`, luồng xử lý và thời gian dự đoán. | Bắt buộc |
| **F6** | Trạng thái tải (Loading state) & Thanh tiến trình | Hiển thị skeleton/spinner khi đang chờ API dự đoán 1 ảnh; cập nhật thanh tiến trình % sau khi từng lô nhiều ảnh trả kết quả. | Bắt buộc |
| **F7** | Bắt lỗi & Thông báo (Toast Notification) | Thông báo lỗi thân thiện khi API quá tải, mất mạng hoặc file upload sai định dạng; thông báo thành công khi xuất lịch sử hoàn tất. | Bắt buộc |
| **F8** | Thiết kế Responsive | Tương thích và hiển thị tốt trên các độ phân giải màn hình từ Desktop đến Laptop/Tablet. | Bắt buộc |
| **F9** | Trực quan hóa XAI Heatmap (Grad-CAM Viewer) | Hỗ trợ hiển thị bản đồ nhiệt màu JET trực quan minh bạch hóa đặc trưng nhận diện của mô hình AI, giúp người vận hành biết được mô hình dựa vào đâu để ra quyết định phân loại rác. | Nâng cao |
| **F10** | Đèn báo trạng thái Server & Pre-warming Ping | Khi mở web, `SystemStatusBadge.tsx` gọi `/api/v1/health` với timeout 5 giây và kiểm tra lại sau 30 giây. Sidebar hiển thị Đang kết nối, Sẵn sàng, Hạn chế hoặc Mất kết nối. | Nâng cao |
| **F11** | Thử với ảnh mẫu | Tab **Một ảnh** có năm ảnh mẫu gồm Nhựa, Giấy, Kim loại, Thủy tinh và một tình huống cần kiểm tra thủ công. Ảnh đã chọn xuất hiện trong khung xem trước. Nút **Bắt đầu dự đoán** dùng luồng dự đoán và XAI hiện có. | Nâng cao |
| **F12** | Xuất CSV lượt xử lý nhiều ảnh | Nút dưới bảng tải CSV do trình duyệt tạo. Tệp gồm các ảnh đã có kết quả hoặc lỗi trong lượt hiện tại, kèm tên tệp, loại rác, độ tin cậy, biên khoảng cách, hai ngưỡng, luồng, thời gian xử lý và lỗi từng ảnh. | Nâng cao |
| **F13** | Bảng số liệu theo khoảng ngày | Phần **Xem số liệu theo ngày** có hai ô **Từ ngày**, **Đến ngày**, nút **Xem số liệu** và nút chuyển trang. Mỗi trang hiển thị tối đa 5 ngày, có tổng số ảnh, Tự động và Thủ công. Khoảng ngày này độc lập với bộ lọc biểu đồ. | Nâng cao |
| **F14** | Hai lớp có xác suất cao nhất | Hiển thị tên và xác suất của hai lớp đứng đầu, chênh lệch theo điểm phần trăm và chốt chưa đạt trong luồng **Thủ công**. Có ở kết quả một ảnh, chi tiết của bảng nhiều ảnh và chi tiết bản ghi mới. | Nâng cao |
| **F15** | Chụp ảnh từ điện thoại | Nút **Chụp ảnh** trong tab **Một ảnh** mở trình chụp trên thiết bị hỗ trợ. Ảnh hiện trong khung xem trước để người dùng kiểm tra rồi mới bấm dự đoán. | Nâng cao |
| **F16** | Thống kê bằng biểu đồ | Phần **Thống kê** mặc định đóng với mũi tên hướng lên, mở bằng nút mũi tên và đổi sang hướng xuống. Biểu đồ tải khi phần này được mở. Đã bỏ dòng khoảng thời gian cạnh bộ lọc và tăng nhẹ chữ tiêu đề, chú thích, nhãn trục. Bố cục desktop gồm bốn ô 2 × 2. Ba biểu đồ dùng chung bộ lọc **Hôm nay**, **1 tuần**, **1 tháng**, **3 tháng**. Hôm nay giữ trục 00h–23h, vẽ dữ liệu đến giờ hiện tại và để trống các giờ chưa tới. Biểu đồ đường hiển thị tổng số ảnh, cột dọc so sánh **Tự động** và **Cần kiểm tra**. Donut **Số ảnh theo loại rác** dùng bốn màu riêng, ghi tổng ảnh của bốn loại ở giữa và hiển thị tỷ lệ của từng phần. Ô cuối trình bày đặc điểm bốn loại rác. Khi đổi bộ lọc, cập nhật giá trị và trục trong cùng kích thước khung. Hover, chạm hoặc focus vào giá trị hiển thị số ảnh và tỷ trọng. Donut tính tỷ trọng trên tổng bốn loại hiển thị, hai biểu đồ thời gian tính trên tổng ảnh trong khoảng. Khoảng 1 tuần và 1 tháng dùng từng ngày, khoảng 3 tháng dùng từng tuần. | Nâng cao |
| **F17** | Ba thẻ tổng quan dự đoán | Hiển thị **Số lượng ảnh dự đoán**, **Số lượng ảnh phân loại tự động**, **Số lượng ảnh phân loại thủ công** thành một hàng phía trên các biểu đồ trên desktop. Ba thẻ dùng chung bộ lọc thời gian với biểu đồ và xếp dọc trên điện thoại. | Nâng cao |

Mỗi lần mở phần **Thống kê**, bộ lọc mặc định là **Hôm nay**. Cỡ chữ nội dung, số liệu, nhãn trục và chú thích được tăng nhẹ để dễ đọc.

---

### 3.5. Yêu cầu Triển khai (Deployment)

| # | Yêu cầu | Chi tiết kỹ thuật | Mức độ |
|---|---|---|---|
| **P1** | Backend deploy trên Render.com từ Monorepo | Nhánh `main`, Root Directory `backend`, Native Python 3.12, gói Free tại Singapore. Cài runtime ONNX qua file lock; `bash start-render.sh` dùng một worker và Auto-Deploy On Commit. | Bắt buộc |
| **P2** | Frontend deploy trên Vercel từ Monorepo | Kết nối cùng 1 repository GitHub, thiết lập **Root Directory: `frontend`**, build tự động Next.js 16 với domain production. | Bắt buộc |
| **P3** | ImageKit Image Storage đã kích hoạt | Cấu hình ImageKit để upload ảnh gốc, ảnh Grad-CAM và ảnh Spatial Energy; API trả URL các ảnh. | Bắt buộc |
| **P4** | Database Supabase (PostgreSQL) đã kích hoạt | Backend đã kết nối và đọc/ghi lịch sử từ bảng `prediction_logs` qua `supabase-py`. | Bắt buộc |
| **P5** | Cấu hình biến môi trường và Secret File | Vercel đặt `NEXT_PUBLIC_API_URL`. Render đặt kết nối Supabase, ImageKit, CORS và Secret File `onnx-model-key`. | Bắt buộc |
| **P6** | Thiết lập CORS Middleware | Backend cho phép domain frontend Vercel gọi API mà không gặp lỗi bảo mật Cross-Origin. | Bắt buộc |
| **P7** | Giám sát UptimeRobot | **Đã kích hoạt monitor Render.** Monitor riêng cho Supabase chưa cấu hình, xem mục 7.6. | Nâng cao |

---

## 4. Sản phẩm nộp bài (Mô hình Monorepo)

### 4.1. Source code (1 GitHub Repository duy nhất)
Dự án áp dụng mô hình **Monorepo** với một [repository GitHub](https://github.com/Silas1502/Trash_Classification).
- Chứa toàn bộ mã nguồn cả `backend/` và `frontend/` trong cùng 1 repository.
- Cấu hình CI/CD độc lập:
  - **Render** kết nối repo và trỏ **Root Directory** vào thư mục `backend`.
  - **Vercel** kết nối repo và trỏ **Root Directory** vào thư mục `frontend`.
- Không cần quản lý 2 repo rời rạc, đồng bộ mã nguồn phiên bản duy nhất.

**Yêu cầu mã nguồn:**
- Có file `README.md` hướng dẫn chi tiết các bước cài đặt và chạy thử nghiệm local.
- Có file `.gitignore` chuẩn (không push file nặng `checkpoints/`, `node_modules/`, `.env`, `__pycache__/`).
- Mã nguồn được module hóa rõ ràng, sạch sẽ, có chú thích đầy đủ.

### 4.2. Đường dẫn Production (URLs)
- **Frontend URL (Vercel):** `https://trash-classification-seven.vercel.app`
- **Backend API URL (Render):** `https://trash-onnx-free-probe.onrender.com/api/v1`
- **Swagger UI (Interactive API Docs):** `https://trash-onnx-free-probe.onrender.com/docs`

### 4.3. Kịch bản Demo thực nghiệm
1. **Demo Phân loại 1 ảnh:** Tải một ảnh rác rồi kiểm tra loại rác, hai thanh **Độ tin cậy** và **Biên khoảng cách** có ngưỡng trong ngoặc, luồng xử lý, trạng thái và gợi ý.
2. **Demo Phân loại theo thư mục:** Chọn một thư mục nhiều ảnh rác $\rightarrow$ Quan sát thanh tiến trình chạy và danh sách ảnh được xử lý đổ vào bảng dữ liệu.
3. **Demo Tra cứu Lịch sử:** Lọc theo loại rác hoặc luồng xử lý, mở chi tiết để xem ba ảnh từ ImageKit, rồi nhấn *Xuất lịch sử* để tải CSV.
4. **Demo ảnh mẫu và hai chốt:** Chạy một ảnh mẫu đại diện và ảnh **Tình huống cần kiểm tra**. Đối chiếu hai lớp đứng đầu, biên khoảng cách và lý do chuyển luồng. Mở hai ảnh XAI.
5. **Demo báo cáo và điện thoại:** Xuất CSV ngay dưới bảng **Nhiều ảnh**, chọn khoảng ngày trong **Lịch sử** để xem thống kê, rồi chụp thử một ảnh trên điện thoại và kiểm tra ảnh xem trước.

---

## 5. Tiêu chí chấm điểm & Nghiệm thu (100 Điểm)

| Hạng mục | Điểm | Tiêu chí chi tiết |
|:---|:---:|:---|
| **1. ML Model & Hệ thống 2 Chốt & XAI** | **20** | |
| - Nạp model ConvNeXt-Tiny & Tiền xử lý ảnh ($320 \times 320$ AREA) | 6 | Model chạy suy luận ổn định, output xác suất Softmax chuẩn xác |
| - Phân luồng theo hai chốt cơ sở | 7 | Cả hai chốt đạt thì vào luồng Tự động. Một chốt chưa đạt thì vào luồng Thủ công và trả lý do tương ứng. Kiểm thử cả trường hợp từng chốt trượt riêng và cả hai cùng trượt. |
| - Gợi ý hành động xử lý rác tương ứng loại rác | 3 | Gợi ý đúng loại thùng rác (tái chế, hữu cơ, vô cơ...) |
| - Trực quan hóa giải thích XAI (Grad-CAM & Spatial Energy) | 4 | Trích xuất thành công bản đồ nhiệt JET Overlay minh bạch hóa nhận diện |
| **2. Backend API (FastAPI)** | **25** | |
| - Endpoint `/predict/single` và `/predict/batch` | 10 | Nhận ảnh đơn & danh sách ảnh, xử lý trả kết quả giá trị đo, ngưỡng, cờ đạt ngưỡng, luồng và trạng thái cho từng ảnh |
| - Endpoint `/history`, `/history/{id}` và `/history/export` | 8 | Lấy lịch sử có phân trang, xem chi tiết và xuất file CSV thành công |
| - Pydantic Validation & Health Check `/health` | 4 | Validate định dạng ảnh chặt chẽ, báo trạng thái hệ thống |
| - CORS & Quản lý Exception tập trung | 3 | Kết nối an toàn, format lỗi chuẩn HTTP |
| **3. Database & Cloud Storage** | **15** | |
| - Tích hợp ImageKit lưu trữ ảnh gốc, Grad-CAM và Spatial Energy | 8 | Ba ảnh có URL truy cập từ ImageKit |
| - Tích hợp Supabase PostgreSQL lưu lịch sử | 7 | Lưu đủ trường nghiệp vụ, lọc và phân trang được |
| **4. Frontend (Next.js 16)** | **25** | |
| - Màn hình Phân loại 1 ảnh (Tab "Một ảnh") | 6 | Khớp chính xác thiết kế: Dropzone, Preview, Card kết quả, hai thanh chỉ số hiển thị phần trăm kèm ngưỡng |
| - Màn hình Phân loại thư mục (Tab "Nhiều ảnh") | 6 | Khớp chính xác: 4 thẻ tiến độ, progress bar, bảng kết quả có tìm kiếm & lọc |
| - Màn hình Lịch sử và cửa sổ chi tiết | 7 | Lọc và phân trang được. Bấm một dòng mở cửa sổ chi tiết với ảnh, hai chỉ số kèm ngưỡng và luồng xử lý. |
| - Trực quan hóa XAI Heatmap Viewer | 3 | Chuyển đổi giữa ảnh gốc, Grad-CAM và Spatial Energy |
| - UI/UX, Sidebar cố định & Responsive | 3 | Giao diện đồng bộ tông xanh navy, hiệu ứng mượt mà |
| **5. Triển khai Cloud & Code Quality** | **15** | |
| - Triển khai Production live (Vercel + Render + ImageKit + Supabase) | 8 | Toàn bộ luồng hoạt động thông suốt trên internet |
| - Code Quality, Cấu trúc dự án & Git Commits | 4 | Code có cấu trúc chuẩn, tách file hợp lý, commit rõ ràng |
| - Tài liệu README.md & Hướng dẫn cài đặt | 3 | Hướng dẫn rõ ràng từ biến môi trường đến chạy local |

---

## 6. Lộ trình thực hiện & Phân chia công việc

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                                 LỘ TRÌNH THỰC HIỆN DỰ ÁN                               │
├─────────────────────┬──────────────────────────────────────────┬───────────────────────┤
│ Giai đoạn           │ Nội dung công việc chính                 │ Sản phẩm bàn giao     │
├─────────────────────┼──────────────────────────────────────────┼───────────────────────┤
│ **Giai đoạn 1**     │ • Thiết lập ImageKit & Project Supabase. │ • ImageKit & Supabase │
│ *(Ngày 1 - 2)*     │ • Chuẩn bị bảng lịch sử và mô hình.      │   Adapter             │
│                     │ • Đóng gói hàm suy luận ConvNeXt-Tiny.   │ • Module nạp mô hình │
│                     │ • Triển khai hai chốt cơ sở để phân luồng│ • Module Hai Chốt    │
│                     │   Tự động / Thủ công theo ngưỡng.        │                       │
├─────────────────────┼──────────────────────────────────────────┼───────────────────────┤
│ **Giai đoạn 2**     │ • Khởi tạo FastAPI App, Pydantic schemas.│ • Hoàn thiện Backend  │
│ *(Ngày 3 - 4)*      │ • Xây dựng API `/predict/single` và      │   FastAPI với đầy đủ  │
│                     │   `/predict/batch`.                      │   Swagger UI `/docs`  │
│                     │ • Xây dựng API `/history` có phân trang, │                       │
│                     │   lọc và export file CSV.                │                       │
├─────────────────────┼──────────────────────────────────────────┼───────────────────────┤
│ **Giai đoạn 3**     │ • Khởi tạo Next.js 16, Tailwind CSS.     │ • Giao diện hoàn chỉnh│
│ *(Ngày 5 - 7)*      │ • Dựng Sidebar xanh navy cố định.        │   khớp 4 ảnh mẫu      │
│                     │ • Dựng Tab 1 ảnh & Tab Nhiều ảnh.        │ • Kết nối Axios API   │
│                     │ • Dựng Trang Lịch sử và cửa sổ xem       │                       │
│                     │   chi tiết kết quả ảnh từ ImageKit.      │                       │
├─────────────────────┼──────────────────────────────────────────┼───────────────────────┤
│ **Giai đoạn 4**     │ • Tích hợp End-to-End Frontend - Backend.│ • Hệ thống Production │
│ *(Ngày 8 - 9)*      │ • Triển khai Vercel, Render, ImageKit,   │   Vercel & Render &   │
│                     │   Supabase.                              │   Supabase + ImageKit │
│                     │ • Kiểm thử và nghiệm thu luồng demo.    │ • Báo cáo nghiệm thu  │
└─────────────────────┴──────────────────────────────────────────┴───────────────────────┘
```

---

## 7. Hướng dẫn chi tiết: Tạo Project, lấy Key/Link và kết nối Fullstack (FE - BE - DB & Cloud Storage)

Hệ thống được thiết kế theo mô hình **Monorepo (1 GitHub repository duy nhất)** chứa cả thư mục `backend/` và `frontend/`. Dưới đây là hướng dẫn từng bước để thiết lập tài nguyên đám mây, lấy khóa truy cập và kết nối 4 thành phần thành một hệ thống hoàn chỉnh.

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                        KIẾN TRÚC KẾT NỐI MONOREPO FULLSTACK                            │
│                                                                                        │
│     ┌────────────────────────────────────────────────────────────────────┐             │
│     │               GITHUB REPOSITORY (1 REPO MONOREPO)                  │             │
│     │   ├── 📂 backend/   ────────────────────────┐                      │             │
│     │   └── 📂 frontend/  ────────────┐           │                      │             │
│     └─────────────────────────────────┼───────────┼──────────────────────┘             │
│                                       ▼           ▼                                    │
│                             ┌───────────┐       ┌───────────┐                          │
│                             │  VERCEL   │       │  RENDER   │                          │
│                             │(Root: frontend) │    │(Root: backend)│                   │
│                             └─────┬─────┘       └─────┬─────┘                          │
│                                   │                   │                                │
│                     NEXT_PUBLIC_API_URL               │                                │
│                                   │                   │                                │
│                                   ▼                   ▼                                │
│                              Gọi REST API     ┌───────────────┐                        │
│                              Gọi REST API     │   ImageKit    │                        │
│                              (Multipart POST) │  (Ảnh & XAI)   │ (Upload & Link ảnh CDN) │
│                                       │       └───────────────┘                        │
│                                       │               ▲                                │
│                                       ▼               │                                │
│                               ┌───────────────┐       │                                │
│                               │   Supabase    │◀──────┘                                │
│                               │ (PostgreSQL)   │                                        │
│                               │  (Lưu DB Log) │                                        │
│                               └───────────────┘                                        │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

### 7.1. Cấu hình Supabase & Lấy SUPABASE_URL + SUPABASE_KEY (Kèm SQL tạo bảng)

Supabase cung cấp PostgreSQL để lưu bảng lịch sử `prediction_logs`. [Hạn mức gói Free](https://supabase.com/pricing)

#### Bước 1: Tạo tài khoản & Project trên Supabase
1. Truy cập [https://supabase.com/](https://supabase.com/) $\rightarrow$ Chọn **Start your project** $\rightarrow$ Đăng nhập bằng GitHub hoặc Google.
2. Nhấn nút **New Project**:
   - **Organization:** Chọn tổ chức mặc định của bạn.
   - **Name:** Chọn tên cho project Supabase.
   - **Database Password:** Nhập mật khẩu mạnh (hãy lưu lại mật khẩu này).
   - **Region:** Chọn `Southeast Asia (Singapore)` để tối ưu tốc độ kết nối về Việt Nam.
3. Nhấn **Create new project** và chờ database khởi tạo.

#### Bước 2: Chạy câu lệnh SQL tạo bảng `prediction_logs`
1. Trong menu bên trái của Supabase Dashboard, chọn biểu tượng **SQL Editor**.
2. Nhấn **New query** và dùng SQL dưới đây khi tạo bảng mới. Cấu hình RLS và quyền đọc/ghi phù hợp với khóa backend. [Tài liệu bảo mật dữ liệu Supabase](https://supabase.com/docs/guides/database/secure-data)
   ```sql
   create table if not exists prediction_logs (
       id uuid primary key,
       file_name text not null,
       image_url text,
       xai_overlay_url text,
       xai_energy_overlay_url text,
       waste_type text not null,
       confidence double precision not null,
       margin double precision not null,
       checkpoint_1 double precision not null,
       checkpoint_2 double precision not null,
       confidence_gate_passed boolean not null,
       margin_gate_passed boolean not null,
       composite_score double precision not null,
       tta_stability double precision,
       decision_tier text not null,
       decision text not null,
       pipeline_type text not null,
       status text not null,
       reason text,
       suggestion text,
       is_mock boolean default false,
       created_at timestamptz default now(),
       metadata jsonb
   );

   create index if not exists idx_prediction_logs_created_at on prediction_logs (created_at desc);
   create index if not exists idx_prediction_logs_waste_type on prediction_logs (waste_type);
   create index if not exists idx_prediction_logs_pipeline_type on prediction_logs (pipeline_type);
   ```
3. Nhấn nút **Run** (màu xanh lá) để thực thi. Bạn sẽ thấy thông báo `Success. No rows returned`.

#### Bước 3: Lấy Project URL và API Key
1. Trong menu bên trái, bấm vào biểu tượng bánh răng **Project Settings** $\rightarrow$ Chọn mục **API**.
2. Tại mục **Project API keys**, bạn copy:
   - **Project URL:** Có dạng `https://xxxxxxxxxxxxxxxxxxxx.supabase.co` $\rightarrow$ Điền vào `SUPABASE_URL`.
   - **Khóa cho backend:** Điền vào `SUPABASE_KEY` và dùng quyền đọc, ghi phù hợp với cấu hình truy cập của dự án. Lưu khóa ở môi trường backend.

---

### 7.2. Cấu hình ImageKit.io & Lấy API Credentials (IMAGEKIT_PUBLIC_KEY, PRIVATE_KEY, URL_ENDPOINT)

ImageKit Forever Free công bố **3 GB lưu trữ** và **20 GB băng thông mỗi tháng**. [Bảng giá ImageKit](https://imagekit.io/plans)

#### Bước 1: Đăng ký tài khoản miễn phí
1. Truy cập [https://imagekit.io](https://imagekit.io) $\rightarrow$ Nhấn **Sign Up for FREE**.
2. Chọn **Continue with Google** $\rightarrow$ Đăng nhập tài khoản Gmail.
3. Đặt ID định danh dịch vụ (Subdomain) $\rightarrow$ Nhấn *Continue*.

#### Bước 2: Lấy 3 thông số API Credentials
1. Tại menu bên trái Dashboard, bấm vào mục **Developer options** (biểu tượng code `< >`).
2. Copy 3 thông số:
   - **URL-endpoint:** Có dạng `https://ik.imagekit.io/xxxxxxxxx` $\rightarrow$ Điền vào `IMAGEKIT_URL_ENDPOINT`.
   - **Public Key:** Bắt đầu bằng `public_...` $\rightarrow$ Điền vào `IMAGEKIT_PUBLIC_KEY`.
   - **Private Key:** Bắt đầu bằng `private_...` $\rightarrow$ Điền vào `IMAGEKIT_PRIVATE_KEY`.
3. Điền các biến vào môi trường backend. Khi chạy local, dùng `backend/.env`. Khi deploy, đặt trong **Render → Environment**. URL ảnh có dạng:
   ```text
   https://ik.imagekit.io/<ID>/uploads/...
   ```

---

### 7.3. Cấu hình triển khai Backend FastAPI trên Render (từ Monorepo)

Render hỗ trợ triển khai trực tiếp từ một thư mục con trong Monorepo thông qua cấu hình **Root Directory**.

#### Bước 1: Tạo Web Service mới trên Render
1. Truy cập [https://dashboard.render.com/](https://dashboard.render.com/) $\rightarrow$ Đăng nhập bằng tài khoản GitHub chứa mã nguồn dự án.
2. Nhấn nút **New +** ở góc trên cùng $\rightarrow$ Chọn **Web Service**.
3. Chọn **Build and deploy from a Git repository** $\rightarrow$ Nhấn Next.
4. Chọn repository `Silas1502/Trash_Classification`.

#### Bước 2: Cài đặt Monorepo & Build Settings
Cấu hình các trường thông tin chính xác như sau:
- **Name:** `trash-onnx-free-probe`
- **Region:** `Singapore (Southeast Asia)`
- **Branch:** `main`
- **Root Directory:** Nhập chính xác: **`backend`** *(Rất quan trọng: Chỉ thị cho Render chỉ đọc và build thư mục `backend/`)*.
- **Runtime:** Native Python 3.12, cấu hình phiên bản trong `backend/.python-version`.
- **Build Command:** `python -m pip install -r onnx_fp32/requirements-runtime.lock.txt`
- **Start Command:** `bash start-render.sh`
- **Instance Type:** Free, giới hạn RAM **512 MiB** cho toàn container.
- **Auto-Deploy:** On Commit.

#### Bước 3: Thêm Biến môi trường (Environment Variables) trên Render
Chuyển sang tab **Environment** trên Render và thêm các biến sau:

| Key | Giá trị mẫu / Hướng dẫn |
|:---|:---|
| `MAX_PREDICTION_REQUESTS` | `1` |
| `INFERENCE_BATCH_SIZE` | `1` |
| `SUPABASE_URL` | URL Supabase lấy ở Bước 7.1 (`https://xxx.supabase.co`) |
| `SUPABASE_KEY` | Khóa backend có quyền đọc, ghi bảng theo cấu hình Supabase |
| `IMAGEKIT_PUBLIC_KEY` | Public Key lấy ở Bước 7.2 |
| `IMAGEKIT_PRIVATE_KEY` | Private Key lấy ở Bước 7.2 |
| `IMAGEKIT_URL_ENDPOINT` | URL Endpoint lấy ở Bước 7.2 (`https://ik.imagekit.io/...`) |
| `STORAGE_CONCURRENCY` | `1` |
| `CORS_ORIGINS` | `["http://localhost:3000", "https://trash-classification-seven.vercel.app"]` |
| `ONNX_UPLOAD_MEMORY_LOG` | `1` để log RAM trước và sau request |
| `ONNX_STARTUP_PROBE` | `0` |
| Secret File `onnx-model-key` | Khóa giải mã bộ tệp trong `backend/model-parts/`. Script kiểm tra SHA256 trước khi nạp ONNX. |

#### Bước 4: Hướng dẫn chi tiết cách tìm, lấy và cấu hình các Đường dẫn (URLs) từ Render Dashboard

Sau khi Render tạo Web Service thành công, giao diện Dashboard của Render sẽ cung cấp các đường dẫn quan trọng cần thiết để vận hành, giám sát và kết nối Backend:

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                              RENDER DASHBOARD GIAO DIỆN                                │
│                                                                                        │
│  [Web Service] trash-onnx-free-probe    ● Live                                           │
│  🔗 https://trash-onnx-free-probe.onrender.com   [📋 Copy URL] ◀── (1) Public URL  │
│                                                                                        │
│  [Events]   [Logs]   [Metrics]   [Environment]   [Settings] ◀────────── (3) Cài đặt   │
│                                                       │                                │
│                                                       ├─► Health Check Path:           │
│                                                       │   /api/v1/health               │
│                                                       │                                │
│                                                       └─► Deploy Hooks:                │
│                                                           https://api.render.com/...   │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

1. **Đường dẫn Web Service URL chính (Public Base URL):**
   - **Vị trí:** Link ngay bên dưới tên dịch vụ `trash-onnx-free-probe`.
   - **Cách lấy:** Nhấp trực tiếp vào biểu tượng **Copy** cạnh link hoặc click chuột phải chọn *Copy link address*.
   - **Định dạng đường dẫn:**
     ```text
     https://trash-onnx-free-probe.onrender.com
     ```
   - **Mục đích sử dụng:**
     - Dùng làm URL gốc (Base URL) cho toàn bộ API backend.
     - Cung cấp cho Frontend trên Vercel: Cấu hình biến môi trường `NEXT_PUBLIC_API_URL = https://trash-onnx-free-probe.onrender.com/api/v1`.
     - Dùng cho Postman / cURL để kiểm thử API từ bên ngoài.

2. **Đường dẫn Swagger UI & ReDoc (Tài liệu API tương tác):**
   - **Cách ghép link:** Lấy Web Service URL ở trên và ghép thêm đuôi `/docs` hoặc `/redoc`:
     - **Swagger UI:** `https://trash-onnx-free-probe.onrender.com/docs`
     - **ReDoc:** `https://trash-onnx-free-probe.onrender.com/redoc`
   - **Mục đích sử dụng:** Mở trực tiếp trên trình duyệt để kiểm tra danh sách API, thử nghiệm upload file ảnh vào endpoint `POST /predict/single` và xem kết quả trả về ngay lập tức.

3. **Cấu hình đường dẫn Health Check Path trên Render:**
   - **Vị trí cài đặt:** Vào tab **Settings** của Web Service $\rightarrow$ Cuộn xuống mục **Health Check Path**.
   - **Đường dẫn cần nhập:** Nhập chính xác:
     ```text
     /api/v1/health
     ```
   - **Mục đích sử dụng:** Render gọi endpoint để kiểm tra dịch vụ. Đọc trạng thái trong JSON để xác định tình trạng Supabase và ImageKit.

4. **Đường dẫn Deploy Hook (Kích hoạt Build tự động từ xa):**
   - **Vị trí lấy nếu dùng CI/CD riêng:** Vào **Settings → Deploy Hooks**. URL chứa khóa, lưu riêng khỏi mã nguồn.
   - **Định dạng đường dẫn:**
     ```text
     https://api.render.com/deploy/srv-xxxxxxxxxxxxxxxx?key=yyyyyyyy
     ```
   - **Mục đích sử dụng:** Deploy Hook có thể kích hoạt deploy từ CI/CD. Dịch vụ hiện dùng **Auto-Deploy On Commit** khi có thay đổi trong `backend/` trên `main`.

5. **Đường dẫn Cổng nội bộ (Internal Port & Environment Variable):**
   - Render cấp biến môi trường `PORT`; script dùng giá trị dự phòng `10000` nếu biến vắng mặt.
   - Lệnh khởi chạy thực tế:
     ```bash
     bash start-render.sh
     ```
   - Script giải mã mô hình vào thư mục tạm và khởi động Uvicorn với một worker. Kiểm tra **Logs** để xác nhận nạp mô hình thành công.

---

### 7.4. Cấu hình triển khai Frontend Next.js trên Vercel (từ Monorepo)

Vercel được tối ưu hóa xuất sắc cho Next.js và hỗ trợ tính năng chọn thư mục gốc (Root Directory) cho Monorepo rất mượt mà.

#### Bước 1: Import Project vào Vercel
1. Truy cập [https://vercel.com/](https://vercel.com/) $\rightarrow$ Đăng nhập bằng tài khoản GitHub.
2. Tại trang Tổng quan (Dashboard), nhấn **Add New...** $\rightarrow$ Chọn **Project**.
3. Tìm `Silas1502/Trash_Classification` rồi nhấn **Import**.

#### Bước 2: Thiết lập Monorepo Root Directory trên Vercel
1. **Project Name:** `trash-classification`.
2. **Framework Preset:** Vercel tự động nhận diện là `Next.js`.
3. **Root Directory (Cốt lõi):**
   - Mặc định Vercel chọn `./`.
   - Nhấn nút **Edit** bên cạnh $\rightarrow$ Chọn thư mục: **`frontend`** $\rightarrow$ Nhấn **Continue**.
4. Các mục *Build Command* và *Output Directory* giữ nguyên mặc định.

#### Bước 3: Thiết lập Biến môi trường trên Vercel
Mở rộng mục **Environment Variables** và cấu hình:
- **Key:** `NEXT_PUBLIC_API_URL` áp dụng cho **Production**.
- **Value:** `https://trash-onnx-free-probe.onrender.com/api/v1` *(Dán URL Backend đã lấy ở Bước 7.3 kèm tiền tố `/api/v1`)*.

#### Bước 4: Deploy & Lấy URL Frontend
1. Nhấn nút **Deploy**.
2. Vercel sẽ tự động tải các packages trong `frontend/package.json` và build ứng dụng Next.js.
3. Khi bản Production báo **Ready**, mở URL đang dùng:
   ```text
   https://trash-classification-seven.vercel.app
   ```

---

### 7.5. Hoàn tất kết nối Fullstack khép kín (Handshake & CORS)

Để Frontend trên Vercel có thể gọi sang Backend trên Render mà không bị trình duyệt chặn bởi chính sách CORS (Cross-Origin Resource Sharing), thực hiện bước bắt tay cuối cùng:

#### Bước 1: Cập nhật CORS trên Render Backend
1. Mở lại Dashboard Render và chọn `trash-onnx-free-probe`.
2. Chọn tab **Environment** $\rightarrow$ Tìm biến `CORS_ORIGINS`.
3. Cập nhật thêm URL Frontend Vercel vào mảng:
   ```json
   ["http://localhost:3000", "https://trash-classification-seven.vercel.app"]
   ```
4. Chọn **Save and deploy** để áp dụng biến môi trường cho bản đang chạy.

#### Bước 2: Bảng tra cứu toàn bộ Biến môi trường kết nối

| Dịch vụ | Biến môi trường (.env) | Nguồn lấy giá trị | Mục đích sử dụng |
|:---|:---|:---|:---|
| **Vercel (FE)** | `NEXT_PUBLIC_API_URL` | Lấy từ URL Render Backend | Để Axios/Fetch ở Frontend biết địa chỉ gọi API |
| **Render (BE)** | `ADAPTIVE_ASSESSMENT_ENABLED` | `false` | Áp dụng hai chốt cơ sở để phân luồng |
| **Render (BE)** | `CORS_ORIGINS` | Lấy từ URL Vercel Frontend | Cho phép trình duyệt gọi API từ domain Vercel |
| **Render (BE)** | `SUPABASE_URL` | Lấy từ Supabase Project Settings > API | Kết nối lưu và đọc kết quả phân loại từ PostgreSQL |
| **Render (BE)** | `SUPABASE_KEY` | Khóa backend theo quyền của dự án Supabase | Đọc và ghi lịch sử |
| **Render (BE)** | `IMAGEKIT_PUBLIC_KEY` | Lấy từ ImageKit Developer options | Khóa API public |
| **Render (BE)** | `IMAGEKIT_PRIVATE_KEY` | Lấy từ ImageKit Developer options | Khóa bảo mật upload ảnh |
| **Render (BE)** | `IMAGEKIT_URL_ENDPOINT`| Lấy từ ImageKit Developer options | URL Endpoint CDN lưu ảnh |
| **Render (BE)** | Secret File `onnx-model-key` | Khóa giải mã mô hình ONNX | Giải mã `model-parts` khi khởi động |

#### Bước 3: Kịch bản Kiểm tra thông suốt toàn diện (End-to-End Verification)
1. Mở trình duyệt truy cập website Frontend: `https://trash-classification-seven.vercel.app`.
2. **Kiểm tra Phân loại 1 ảnh:**
   - Kéo thả 1 bức ảnh rác thải (ví dụ: chai nhựa `plastic_bottle_01.jpg`).
   - Nhấn **Bắt đầu dự đoán**.
   - Quan sát DevTools (F12) $\rightarrow$ Tab Network: Request gửi đến `...onrender.com/api/v1/predict/single` trả về mã `200 OK`.
   - Kiểm tra ảnh xem trước, hai chỉ số theo dạng `giá trị % (ngưỡng %)` và luồng xử lý. Ảnh đạt cả hai chốt phải vào `Tự động`. Ảnh trượt ít nhất một chốt phải vào `Thủ công`.
3. **Kiểm tra ImageKit Storage:**
   - Mở ảnh gốc, Grad-CAM và Spatial Energy từ chi tiết kết quả.
   - Xác nhận các URL ImageKit mở được và khớp với bản ghi lịch sử.
4. **Kiểm tra Supabase Database:**
   - Vào Supabase Dashboard $\rightarrow$ Table Editor $\rightarrow$ Chọn bảng `prediction_logs`.
   - Bản ghi mới nhất xuất hiện với đầy đủ các trường: `id`, `file_name`, `image_url`, `waste_type`, `confidence`, `checkpoint_1`, `checkpoint_2`, `pipeline_type`, `status`.
5. **Kiểm tra Trang Lịch sử:**
   - Nhấn vào menu **Lịch sử** trên sidebar Frontend.
   - Bản ghi vừa dự đoán hiển thị trong bảng. Mở chi tiết để kiểm tra ảnh, hai chốt, ngưỡng và luồng đã lưu.

Lượt thử PNG 16 MP (2,60 MiB) trên Render Free trả HTTP 200 sau khoảng 16,1 giây từ phía client, đã lưu đủ XAI và lịch sử. RAM toàn container là 350,8 MiB trước và 373,9 MiB sau lượt thử với giới hạn 512 MiB. Đỉnh theo vòng đời container đã chạm giới hạn trước lượt đo; phép thử chưa xác định đỉnh riêng của ảnh. Không ghi nhận sự kiện hết RAM trong lượt thử.

---

### 7.6. Chiến lược UptimeRobot kép

**Monitor Render đã kích hoạt.** Phần A ghi cấu hình và kết quả xác minh giám sát từ bên ngoài. Phần B mô tả đèn trạng thái trên website.
1. **Tầng 1 (UptimeRobot):**
   - **Monitor 1 (Render):** Đang theo dõi phản hồi HTTP từ `/api/v1/health`.
   - **Monitor 2 (Supabase):** Chưa cấu hình riêng. Đánh giá nhu cầu và quyền truy cập trước khi thiết lập.
2. **Tầng 2 (Đã thực hiện):** Frontend gửi `GET /api/v1/health` khi mở trang và hiển thị trạng thái trong Sidebar.

```
┌───────────────────────────────────────────────────────────────┐
│ UptimeRobot                                                   │
│ ├─ Monitor 1 → Render /api/v1/health (đã kích hoạt)             │
│ └─ Monitor 2 → Supabase (chưa cấu hình riêng)                  │
├───────────────────────────────────────────────────────────────┤
│ Luồng hiện tại                                                │
│ Frontend Next.js → /api/v1/health → trạng thái đã lưu          │
│ FastAPI → kiểm tra Supabase và ImageKit theo chu kỳ            │
└───────────────────────────────────────────────────────────────┘
```

---

#### Phần A: Hướng dẫn cấu hình UptimeRobot

##### Bước 1: Đăng ký tài khoản UptimeRobot
Monitor Render được tạo bằng **Quick Monitor Setup**. Chủ tài khoản đã xác nhận kích hoạt qua email. [Hướng dẫn UptimeRobot](https://uptimerobot.com/quick-monitor-setup/)

##### Bước 2: Thiết lập Monitor 1 — Theo dõi Render Backend
- **Mục tiêu:** Theo dõi phản hồi và giữ backend Render thức để giảm thời gian chờ khi mở website. Render Free có thể ngủ sau 15 phút không có lưu lượng vào. [Render Free](https://render.com/docs/free#spinning-down-on-idle)
- **Loại monitor:** HTTP(S), theo dõi mã phản hồi của endpoint.
- **URL:** [Health Render](https://trash-onnx-free-probe.onrender.com/api/v1/health).
- **Gói và chu kỳ:** Quick Monitor Setup mặc định kiểm tra mỗi **5 phút** trên gói Free. Log ngày 18/11/2026 ghi nhận monitor chạy khoảng **5 phút/lần**. Có thể điều chỉnh trong **Monitor interval**. [Tài liệu Quick Monitor Setup](https://uptimerobot.com/quick-monitor-setup/)
- **Giờ chạy Render:** Để giữ backend thức, đặt khoảng kiểm tra dưới 15 phút. Khi hai lịch đều giữ backend chạy liên tục, chúng dùng cùng số giờ Render. Một dịch vụ chạy suốt tháng 31 ngày dùng 744 trong 750 giờ miễn phí dùng chung của workspace. [Hạn mức Render Free](https://render.com/docs/free#monthly-usage-limits)

##### Bước 3: Thiết lập Monitor 2 — Theo dõi Supabase
**Hiện dùng một monitor UptimeRobot cho Render.** Việc kiểm tra kết nối Supabase được thực hiện trong backend theo cơ chế ở Bước 4.

- **Kiểm tra kết nối:** Xem trường `database` trong JSON từ `GET /api/v1/health`. Giá trị `connected` cho biết lần kiểm tra gần nhất thành công.
- **Trạng thái gói Free:** Truy vấn định kỳ tạo hoạt động cho database khi backend chạy. Supabase đánh giá theo mức hoạt động trong một tuần, nên cơ chế này giúp giảm nguy cơ tạm dừng mà không bảo đảm uptime. [Supabase Project Pausing](https://supabase.com/docs/guides/platform/free-project-pausing)

##### Bước 4: Đối chiếu với cơ chế kiểm tra của backend
Khi backend đang chạy, tác vụ nền `_watch_dependencies` kiểm tra Supabase và ImageKit, rồi chờ **30 giây** trước lượt tiếp theo theo giá trị mặc định của `HEALTH_PROBE_INTERVAL_SECONDS`. Lượt kiểm tra Supabase đọc tối đa một `id` từ bảng `prediction_logs`. Đây là cơ chế trong code của dự án. [Tác vụ nền](../backend/app/main.py) · [Truy vấn Supabase](../backend/app/db/supabase_db.py)

Khi UptimeRobot gọi `HEAD /api/v1/health`, backend đọc trạng thái đã lưu và trả mã HTTP. Các truy vấn Supabase diễn ra theo lịch riêng của tác vụ nền, dừng khi backend ngủ hoặc dừng.

##### Bước 5: Xác nhận trạng thái trên UptimeRobot sau khi cấu hình
1. Ngày **18/11/2026 (UTC+7)**, access log Render ghi nhận các lượt UptimeRobot gọi `HEAD /api/v1/health` lúc **08:27, 08:32, 08:38, 08:43 và 08:48**. Cả năm lượt đều trả **HTTP 200**. Nguồn request khớp danh sách IP giám sát chính thức. [Danh sách IP UptimeRobot](https://uptimerobot.com/help/locations/)
2. Kiểm tra riêng bằng `GET /api/v1/health` trả `status=healthy`, `database=connected` và `storage=reachable`. Monitor HTTP hiện kiểm tra mã phản hồi; JSON dùng để xác nhận trạng thái phụ thuộc.

---

#### Phần B: Triển khai Pre-warming Ping & Đèn trạng thái trên Frontend (Tầng Client UX)

- **Mục đích:**
  1. Gửi yêu cầu kiểm tra khi người dùng mở trang.
  2. Hiển thị một chấm đèn trực quan ở chân Sidebar giúp người dùng biết hệ thống đã sẵn sàng trước khi tải ảnh lên.

- **Hàm kiểm tra trạng thái trong [`frontend/src/services/api.ts`](../frontend/src/services/api.ts):**
  ```typescript
  export async function getHealth(signal: AbortSignal) {
    const { data } = await api.get<HealthCheckResponse>("/health", { signal, timeout: 5000 });
    return data;
  }
  ```

- **Component đèn trạng thái trong [`SystemStatusBadge.tsx`](../frontend/src/components/layout/SystemStatusBadge.tsx):**
  ```tsx
  "use client";

  import { useEffect, useState } from "react";
  import { getHealth } from "@/services/api";

  const labels = {
    checking: "Đang kết nối…",
    ready: "Hệ thống: Sẵn sàng",
    degraded: "Hệ thống: Hạn chế",
    offline: "Mất kết nối",
  };

  export default function SystemStatusBadge() {
    const [status, setStatus] = useState<keyof typeof labels>("checking");

    useEffect(() => {
      let active = true;
      let timer: number | undefined;
      const controller = new AbortController();
      async function check() {
        try {
          const health = await getHealth(controller.signal);
          if (active) setStatus(health.status === "healthy" ? "ready" : health.status === "degraded" ? "degraded" : "offline");
        } catch {
          if (active) setStatus("offline");
        } finally {
          if (active) timer = window.setTimeout(check, 30000);
        }
      }
      void check();
      return () => { active = false; controller.abort(); window.clearTimeout(timer); };
    }, []);

    return <div className="system-status" role="status"><span className={"status-dot " + status} />{labels[status]}</div>;
  }
  ```

Frontend hiện chờ tối đa 5 giây cho health check và thử lại sau 30 giây. Lần truy cập đầu khi Render còn đang khởi động có thể hiện **Mất kết nối** trước khi trạng thái chuyển sang **Sẵn sàng**.

---

> 📌 **Ghi chú quan trọng cho Đội ngũ phát triển:**  
> - Đối chiếu giao diện với 4 ảnh tham chiếu trong thư mục [Giao diện](../Giao%20diện).
> - Lưu `SUPABASE_KEY`, `IMAGEKIT_PRIVATE_KEY`, `onnx-model-key` và Deploy Hook trong môi trường dành cho dịch vụ hoặc tệp cục bộ được Git bỏ qua.
