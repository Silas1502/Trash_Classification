# 📋 KẾ HOẠCH XÂY DỰNG HỆ THỐNG FULLSTACK WEB PHÂN LOẠI RÁC THẢI (TRASH CLASSIFICATION APP)

> **Dự án:** Ứng dụng Web Phân loại rác thải tự động ứng dụng Deep Learning, Hệ thống kiểm soát an toàn 2 Chốt chặn (Two-Gate Safety) và Lưu trữ Đám mây (Supabase + Cloudinary / MongoDB + R2)  
> **Quy chuẩn định dạng:** Kế thừa cấu trúc từ [DE_BAI_MINI_PROJECT.md](./docs/DE_BAI_MINI_PROJECT.md)  
> **Giao diện tham chiếu:** Thư mục [Giao diện](./Giao%20diện)

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
   - [7.6. Chiến lược UptimeRobot Kép: Chống Cold Start Render & Chống Tạm dừng Supabase (Anti-Pause 7 Days)](#76-chiến-lược-kép-chống-cold-start-uptimerobot-keep-alive--frontend-pre-warming-ux)

---

## 1. Tổng quan đề bài & Mục tiêu

### Mô tả dự án
Xây dựng một ứng dụng web **Fullstack** hoàn chỉnh cho bài toán **Phân loại rác thải tự động (Trash Classification App)** ứng dụng Thị giác máy tính và Học sâu (Deep Learning). Hệ thống cho phép người dùng tải lên 1 ảnh đơn lẻ hoặc xử lý hàng loạt theo thư mục ảnh. 

Hệ thống tích hợp mô hình học sâu kết hợp **Hệ thống kiểm soát an toàn 2 Chốt chặn (Two-Gate Safety) & Quy trình Tái thẩm định thích ứng 3 Cấp độ (3-Tier Adaptive Safety Filter)** nhằm tự động đánh giá:
- **Loại rác:** Nhựa, Giấy, Kim loại, Thủy tinh, Hữu cơ, Khác.
- **Độ tin cậy (%):** Xác suất tin cậy của nhãn phân loại cao nhất ($Conf = \max(P)$).
- **Chốt 1 (%):** Điểm đánh giá theo ngưỡng tin cậy an toàn thích ứng riêng từng lớp ($\tau_{conf} = \mu_c - k_1\sigma_c$).
- **Chốt 2 (%):** Điểm đánh giá theo ngưỡng khoảng cách biên phân biệt ($\tau_{margin} = \mu_m - k_2\sigma_m$).
- **Luồng xử lý:** Tự động (`Tu_Dong_Gap` khi vượt qua Cấp 1 Hard Gates, Cấp 2 Bù trừ an toàn hoặc Cấp 3 Bảo lãnh TTA) hoặc Thủ công (`Chuyen_Khay_Thu_Cong` khi có độ bất định cao).
- **Trạng thái:** Thành công (kết quả hợp lệ) hoặc Cần kiểm tra (mẫu cận biên/nghi ngờ vi phạm an toàn).
- **Trí tuệ nhân tạo có thể giải thích (Explainable AI - XAI):** Tích hợp kỹ thuật **Grad-CAM (Gradient-weighted Class Activation Mapping)** và **Spatial Activation Energy Map** để trực quan hóa bản đồ nhiệt (Heatmap Overlay), minh bạch hóa lý do mô hình đưa ra dự đoán phân loại.

Toàn bộ hình ảnh gốc và ảnh phân tích XAI được lưu trữ trên **Cloudinary** (hoặc Cloudflare R2), dữ liệu kết quả được lưu trữ an toàn trên **Supabase** (PostgreSQL) hoặc **MongoDB Atlas**. Cả hai dịch vụ cốt lõi đều hỗ trợ gói Free 100% không yêu cầu thẻ tín dụng, đi kèm hệ thống UptimeRobot kép giữ trạng thái online 24/7.

### Mục tiêu đạt được
- Đóng gói và triển khai mô hình Deep Learning (`ConvNeXt-Tiny` / `ResNet-50`) lên môi trường Web Production.
- Xây dựng RESTful API backend bất đồng bộ hiệu năng cao bằng **FastAPI**.
- Xây dựng giao diện frontend hiện đại, chuẩn xác theo thiết kế bằng **Next.js 14+ (App Router)** và **Tailwind CSS**.
- Tích hợp lưu trữ hình ảnh đám mây tốc độ cao với **Cloudinary** (25GB Free, CDN HTTPS vĩnh viễn, không cần thẻ ngân hàng) hoặc **Cloudflare R2**.
- Thiết kế và truy vấn cơ sở dữ liệu quan hệ **Supabase (PostgreSQL)** hoặc phi quan hệ **MongoDB Atlas** có đánh chỉ mục (Indexing) phục vụ tìm kiếm, phân trang và xuất báo cáo.
- Vận hành cơ chế UptimeRobot kép chống ngủ đông cho cả Render Backend và Supabase Database.
- Nắm vững toàn bộ quy trình phát triển và triển khai sản phẩm phần mềm AI end-to-end.

---

## 2. Yêu cầu kỹ thuật bắt buộc

### 2.1. Tech Stack quy định

| Layer | Công nghệ | Dịch vụ / Hosting | Mô tả chức năng |
|:---|:---|:---|:---|
| **ML Model** | TensorFlow / Keras 3 (`ConvNeXt-Tiny`) | File checkpoint `.keras` / `.h5` | Suy luận phân loại ảnh, tính toán xác suất và khoảng cách biên |
| **Backend** | FastAPI (Python 3.10+) | Render.com / Railway | RESTful API, tiền xử lý ảnh, module 2 chốt chặn, điều phối dữ liệu |
| **Frontend** | Next.js 14+ (React) + TypeScript + Tailwind CSS | Vercel | Giao diện người dùng responsive, kéo thả ảnh/thư mục, hiển thị kết quả |
| **Cloud Storage** | ImageKit.io (chính - 20GB Free) / Supabase / Cloudinary / R2 | ImageKit Cloud | Lưu trữ tập trung toàn bộ hình ảnh rác tải lên & ảnh nhiệt XAI (20GB Free trọn đời, không cần thẻ) |
| **Database** | Supabase (PostgreSQL - chính) / MongoDB Atlas (dự phòng) | Supabase Cloud | Lưu trữ bảng lịch sử `prediction_logs` và kết quả dự đoán (Không cần thẻ ngân hàng) |
| **DevOps / Keep-Alive** | UptimeRobot (Free) | Cloud Service (uptimerobot.com) | Giữ ấm kép: Ping Render Backend (Zero Cold Start) + Ping Supabase REST API (Chống ngủ đông 7 ngày) |
| **Repository** | Monorepo (1 Repo duy nhất) | GitHub | Quản lý chung cả frontend/ và backend/, kết nối độc lập với Render (Root: backend) và Vercel (Root: frontend) |
| **Version Control**| Git + GitHub | GitHub | Quản lý phiên bản mã nguồn dự án |

### 2.2. Kiến trúc luồng dữ liệu bắt buộc

```
┌────────────────────────┐      ┌─────────────────────────┐      ┌────────────────────────┐
│   Frontend (Next.js)   │────▶│    FastAPI Backend      │────▶│   Cloudinary Storage   │
│  - Tab 1 ảnh           │◀────│  - Image Preprocess      │◀────│ (hoặc Cloudflare R2)   │
│  - Tab nhiều ảnh       │      │  - Model Inference      │      │ (Lưu trữ ảnh & XAI)    │
│  - Trang Lịch sử       │      │  - Two-Gate Safety Core │      └────────────────────────┘
└────────────────────────┘      └─────────────────────────┘                  │
         ▲                                   │                               │ URL ảnh
         │                                   │                               ▼
         │                                   │                   ┌────────────────────────┐
         │                                   └──────────────────▶│   Supabase Database    │
         └───────────────────────────────────────────────────────│ (hoặc MongoDB Atlas)   │
                       Hiển thị dữ liệu & Ảnh CDN                │ (Lưu log kết quả phân) │
                                                                 └────────────────────────┘
```

---

## 3. Yêu cầu chức năng chi tiết

### 3.1. Cấu trúc thư mục dự án

```text
TRASH_CLASSIFICATION_SYSTEM/
├── 📂 backend/                                # [B1-B11] Source code FastAPI Backend
│   ├── 📂 app/
│   │   ├── 📂 api/
│   │   │   └── 📂 v1/
│   │   │       ├── 📂 endpoints/
│   │   │       │   ├── predict.py            # API /predict/single, /predict/batch
│   │   │       │   ├── history.py            # API /history, /history/{id}, /history/export
│   │   │       │   └── system.py             # API /health, /model-info
│   │   │       └── router.py                 # Định tuyến tổng hợp API v1
│   │   ├── 📂 core/
│   │   │   ├── config.py                     # Quản lý cấu hình & biến môi trường (.env)
│   │   │   ├── safety_thresholds.json        # File JSON chứa toàn bộ ngưỡng an toàn trích xuất từ Notebook (Cell 13)
│   │   │   └── safety_gate.py                # Đọc safety_thresholds.json, vận hành Tái thẩm định thích ứng 3 cấp độ
│   │   ├── 📂 db/
│   │   │   ├── supabase_db.py        # Adapter Supabase PostgreSQL (REST API & Auth key)
│   │   │   ├── cloudinary_storage.py # Adapter Cloudinary Upload & CDN URL
│   │   │   ├── mongodb.py            # (Dự phòng) Kết nối Motor Async MongoDB Driver
│   │   │   └── r2_storage.py         # (Dự phòng) Client Boto3 Cloudflare R2
│   │   ├── 📂 ml/
│   │   │   ├── custom_layers.py              # Định nghĩa lớp CosineDense để nạp model Keras
│   │   │   ├── model_loader.py               # Nạp weights ConvNeXt-Tiny (.keras) & sub_logits_model
│   │   │   ├── preprocessor.py               # Resize 320x320 AREA, chuẩn hóa ConvNeXt
│   │   │   ├── inference.py                  # Hàm suy luận 5-View TTA và Single-View
│   │   │   └── xai_engine.py                 # Trích xuất Grad-CAM & JET Heatmap Overlay
│   │   ├── 📂 schemas/
│   │   │   ├── prediction.py                 # Pydantic Schemas kết quả dự đoán
│   │   │   └── history.py                    # Pydantic Schemas lịch sử & bộ lọc
│   │   └── main.py                           # Khởi tạo FastAPI app, Lifespan nạp model 1 lần, CORS
│   ├── 📂 checkpoints/                       # File trọng số & cấu hình mô hình
│   │   ├── best_trashnet_convnext_retrained.keras
│   │   └── safety_thresholds.json            # Bản sao cấu hình ngưỡng an toàn
│   ├── requirements.txt                      # fastapi, uvicorn, tensorflow, motor, boto3, opencv-python-headless...
│   └── .env.example                          # Mẫu cấu hình môi trường
│
├── 📂 frontend/                               # [F1-F8] Source code Next.js 14+
│   ├── 📂 src/
│   │   ├── 📂 app/                           # App Router (Pages & Layouts)
│   │   │   ├── layout.tsx                    # Root layout chứa Sidebar cố định
│   │   │   ├── page.tsx                      # Landing / Redirect sang /classify
│   │   │   ├── 📂 classify/                  
│   │   │   │   └── page.tsx                  # Trang Phân loại (Tab Một ảnh & Tab Nhiều ảnh)
│   │   │   └── 📂 history/                   
│   │   │       └── page.tsx                  # Trang Lịch sử (Table & Split View xem chi tiết)
│   │   ├── 📂 components/                    # UI Components
│   │   │   ├── 📂 layout/
│   │   │   │   └── Sidebar.tsx               # Sidebar màu xanh navy đậm cố định
│   │   │   ├── 📂 classify/
│   │   │   │   ├── SingleImageUpload.tsx     # Khối kéo thả 1 ảnh + Xem trước (Preview)
│   │   │   │   ├── SingleImageResult.tsx     # Hiển thị Loại rác, 3 thanh Progress, Gợi ý
│   │   │   │   ├── BatchImageUpload.tsx      # Kéo thả nhiều ảnh hoặc chọn thư mục
│   │   │   │   ├── BatchProgressBar.tsx      # 4 thẻ thống kê + Thanh tiến trình thời gian thực
│   │   │   │   └── BatchResultTable.tsx      # Bảng kết quả danh sách ảnh đã xử lý
│   │   │   ├── 📂 history/
│   │   │   │   ├── HistoryFilterBar.tsx      # Bộ lọc tìm kiếm, loại rác, luồng, thời gian
│   │   │   │   ├── HistoryTable.tsx          # Bảng danh sách lịch sử có phân trang
│   │   │   │   └── HistoryDetailPanel.tsx    # Panel chi tiết bên phải (Ảnh lớn Cloudinary/R2 + Chỉ số)
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
│   ├── DE_BAI_MINI_PROJECT.md                # Đề bài chuẩn tham khảo
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

| # | Yêu cầu | Chi tiết kỹ thuật | Mức độ |
|---|---|---|---|
| **B1** | Tạo FastAPI App & Swagger UI | Khởi tạo ứng dụng FastAPI với tài liệu API tự động tại `/docs` (Swagger UI) và `/redoc`. | Bắt buộc |
| **B2** | Health Check (`GET /health`) | Trả về trạng thái hoạt động: Model (`loaded`/`error`), Database Supabase (`connected`/`disconnected`) và Storage Cloudinary (`reachable`). Thiết kế phản hồi siêu nhẹ (< 10ms) phục vụ UptimeRobot Keep-Alive và Frontend Pre-warming ping. | Bắt buộc |
| **B3** | Phân loại 1 ảnh (`POST /predict/single`) | **Quy trình xử lý hoàn chỉnh chuẩn từ `kltn-convnext-tiny.ipynb`:**<br/>1. Nhận file ảnh qua `multipart/form-data`, tải ảnh lên Cloudinary (hoặc R2) lấy URL công khai.<br/>2. **Tiền xử lý dữ liệu chuẩn Deep Learning:**<br/>&nbsp;&nbsp;• *Giải mã & chuẩn màu:* Decode ảnh buffer sang mảng RGB 3 kênh.<br/>&nbsp;&nbsp;• *Smart Auto-Crop / Center Square:* Tách contour căn tâm rác (rembg u2netp) hoặc cắt vuông $(a, a)$ căn giữa tâm để giữ nguyên tỷ lệ 1:1, không méo vật thể.<br/>&nbsp;&nbsp;• *Tái định cỡ quang học (Area Resampling):* Resize về kích thước chuẩn $(320, 320)$ bằng thuật toán `ResizeMethod.AREA` (kèm `antialias=True`) chống răng cưa.<br/>&nbsp;&nbsp;• *Chuẩn hóa ConvNeXt:* Chuyển sang `float32` và chuẩn hóa qua `preprocess_convnext`.<br/>&nbsp;&nbsp;• *Suy luận TTA / Single-View:* Đưa qua tầng `CosineDense(scale=20.0)` thu logits và tính xác suất Softmax (hỗ trợ 5-View TTA ensemble).<br/>3. **Hệ thống kiểm soát an toàn 2 Chốt & Quy trình Tái thẩm định thích ứng 3 Cấp độ:** Đánh giá lần lượt Cấp 1 (Hard Standard Gates), Cấp 2 (Composite Safety Rescue), Cấp 3 (TTA Consensus Rescue) $\rightarrow$ Định tuyến luồng `Tự động`/`Thủ công`, trạng thái `Thành công`/`Cần kiểm tra`.<br/>4. **XAI Grad-CAM:** Trích xuất Activation Heatmap Overlay và upload lên Cloudinary (hoặc R2).<br/>5. Ghi dữ liệu vào Supabase PostgreSQL (hoặc MongoDB Atlas) và trả về response cho client. | Bắt buộc |
| **B4** | Phân loại nhiều ảnh / thư mục (`POST /predict/batch`) | Nhận danh sách nhiều file ảnh (`List[UploadFile]`). Upload ảnh song song lên Cloudinary, thực hiện suy luận theo batch để tối ưu tốc độ GPU/CPU, đánh giá an toàn qua Quy trình tái thẩm định thích ứng 3 cấp độ cho từng ảnh và ghi đồng thời vào Supabase Database. Trả về kết quả danh sách kèm thống kê tiến độ. | Bắt buộc |
| **B5** | Hệ thống kiểm soát an toàn 2 Chốt & Quy trình Tái thẩm định thích ứng 3 Cấp độ (3-Tier Adaptive Safety Filter) | **Chuẩn thuật toán từ `docs/Luong_hoat_dong.md` (Mục 7) & Cell 10 notebook (Nạp động từ `safety_thresholds.json` - Cell 13):**<br/>1. **6 trường kết quả cốt lõi + trường giải trình an toàn:**<br/>&nbsp;&nbsp;• **Loại rác:** Nhựa, Giấy, Kim loại, Thủy tinh, Hữu cơ, Khác.<br/>&nbsp;&nbsp;• **Độ tin cậy (%):** Điểm xác suất Softmax Top-1 ($Conf = \max(P)$).<br/>&nbsp;&nbsp;• **Chốt 1 (%):** Ngưỡng tin cậy thích ứng riêng từng lớp ($\tau_{conf} = \mu_c - k_1\sigma_c$).<br/>&nbsp;&nbsp;• **Chốt 2 (%):** Ngưỡng biên phân biệt chung ($\tau_{margin} = \mu_m - k_2\sigma_m$, với $Margin = Conf_{Top1} - Conf_{Top2}$).<br/>&nbsp;&nbsp;• **Luồng xử lý:** `Tự động` hoặc `Thủ công`.<br/>&nbsp;&nbsp;• **Trạng thái:** `Thành công` hoặc `Cần kiểm tra`.<br/>2. **Quy trình tái thẩm định thích ứng cho mẫu có độ bất định:**<br/>&nbsp;&nbsp;• *Cấp 1 (Hard Standard Gates):* $Conf \ge \tau_{conf}$ VÀ $Margin \ge \tau_{margin} \rightarrow$ **Tự động** (`Tu_Dong_Gap`).<br/>&nbsp;&nbsp;• *Cấp 2 (Composite Safety Rescue):* $S_{composite} = 0.5 \cdot \frac{Conf}{\tau_{conf}} + 0.5 \cdot \frac{Margin}{\tau_{margin}} \ge 1.0$ VÀ $Conf \ge 70\% \rightarrow$ Cứu nguy bù trừ an toàn $\rightarrow$ **Tự động** (`Tu_Dong_Gap`).<br/>&nbsp;&nbsp;• *Cấp 3 (TTA Consensus Rescue):* $S_{composite} \ge 0.90$ VÀ $TTA\_Stability = 1.0$ (100% 5 view đồng thuận) VÀ $Conf \ge 65\% \rightarrow$ Cứu nguy bảo lãnh đồng thuận $\rightarrow$ **Tự động** (`Tu_Dong_Gap`).<br/>&nbsp;&nbsp;• *Phân luồng thủ công (Manual Fallback):* Không thỏa mãn cấp nào $\rightarrow$ **Thủ công** (`Chuyen_Khay_Thu_Cong`), trạng thái `Cần kiểm tra`, kèm giải trình lý do vi phạm từng chốt. | Bắt buộc |
| **B6** | Input Validation bằng Pydantic | Xác thực định dạng tệp ảnh đầu vào (`image/jpeg`, `image/png`, `image/webp`), kích thước file tối đa cho phép. Trả mã lỗi `400/422` kèm thông báo rõ ràng khi dữ liệu không hợp lệ. | Bắt buộc |
| **B7** | Lấy danh sách lịch sử (`GET /history`) | Truy vấn lịch sử từ Supabase Database (hoặc MongoDB Atlas) hỗ trợ phân trang (`page`, `limit`), sắp xếp giảm dần theo thời gian (`created_at: desc`), lọc theo `waste_type`, `pipeline_type`, khoảng thời gian và tìm kiếm theo tên file. | Bắt buộc |
| **B8** | Chi tiết 1 bản ghi lịch sử (`GET /history/{id}`) | Lấy đầy đủ thông tin chi tiết của 1 lượt dự đoán theo `id`, bao gồm URL hình ảnh từ Cloudinary (hoặc R2), các chỉ số dự đoán và metadata. | Bắt buộc |
| **B9** | Xuất dữ liệu lịch sử (`GET /history/export`) | Xuất toàn bộ dữ liệu lịch sử hoặc dữ liệu sau khi lọc ra file `.csv` hoặc `.xlsx` để người dùng tải về báo cáo. | Nâng cao |
| **B10**| CORS Middleware & Error Handling | Cấu hình middleware CORS cho phép frontend Next.js gọi API; cơ chế bắt lỗi tập trung (Global Exception Handler) chuẩn hóa format lỗi JSON. | Bắt buộc |
| **B11**| Thông tin Model (`GET /model-info`) | Trả về thông tin kiến trúc mô hình (ConvNeXt-Tiny), phiên bản checkpoint, kích thước ảnh đầu vào ($320 \times 320$) và toàn bộ nội dung cấu hình bộ ngưỡng an toàn đọc trực tiếp từ file `safety_thresholds.json`. | Bonus |
| **B12**| Giải thích mô hình với XAI (`Grad-CAM Engine`) | Trích xuất bản đồ kích hoạt không gian (Spatial Activation Map) và Grad-CAM từ tầng tích chập cuối (`convnext_tiny_stage_3_block_2_identity`). Tính toán trọng số gradients, áp dụng Colormap JET và hòa trộn phủ nhiệt (Overlay) lên ảnh gốc ($\alpha = 0.48$). Tự động lưu ảnh phân tích XAI lên Cloudinary (hoặc R2) và trả về URL ảnh phủ nhiệt (`xai_overlay_url`). | Nâng cao |

#### Chi tiết Quy trình Xử lý Dữ liệu trước khi nạp vào Mô hình (Trích xuất từ `kltn-convnext-tiny.ipynb`):
Để đảm bảo mô hình phân loại đạt độ chính xác cao nhất và tương thích hoàn toàn với quá trình huấn luyện trong notebook `kltn-convnext-tiny.ipynb`, pipeline xử lý ảnh trong Backend FastAPI được thực hiện tuần tự qua 5 công đoạn kỹ thuật:

```
┌─────────────────┐      ┌─────────────────────────┐      ┌─────────────────────────┐
│  Raw Image File │────▶│ 1. Giải mã & Chuẩn màu   │────▶│ 2. Smart Auto-Crop      │
│  (UploadFile)   │      │    (Decode -> RGB)      │      │    (Căn tâm rác vuông)  │
└─────────────────┘      └─────────────────────────┘      └─────────────────────────┘
                                                                       │
┌─────────────────────────┐      ┌─────────────────────────┐           │
│ 5. Suy luận 5-View TTA  │◀────│ 4. Chuẩn hóa ConvNeXt    │◀──────────┘
│   & Đánh giá 2 Chốt     │      │ (preprocess_convnext)   │      3. Area Resampling
│ (Softmax + Tau1 + Tau2) │      │ (Zero-mean Unit-var)    │       (320x320 antialias)
└─────────────────────────┘      └─────────────────────────┘
```

1. **Bước 1: Tiếp nhận và giải mã hình ảnh (Image Decoding):**
   - Đọc dữ liệu nhị phân (bytes) từ request tải lên.
   - Giải mã an toàn bằng `cv2.imdecode(np.frombuffer(contents, np.uint8), cv2.IMREAD_COLOR)` và chuyển hệ màu từ BGR sang RGB (`cv2.COLOR_BGR2RGB`), hoặc dùng `tf.image.decode_jpeg(channels=3)` nhằm tránh lỗi Unicode/tiếng Việt và lỗi lệch kênh màu.
2. **Bước 2: Căn chỉnh & Cắt vùng rác trọng tâm (Smart Auto-Crop / Bounding Box Centering):**
   - *Cơ chế Smart Auto-Crop (theo Cell 3):* Sử dụng phiên bản nhẹ `rembg` (session `u2netp`) tách nền rác, lấy alpha mask, tìm contour lớn nhất của đối tượng rác (`contourArea > 20`), xác định tọa độ tâm đối tượng $(c_x, c_y)$.
   - *Cắt vuông bảo toàn tỷ lệ:* Cắt khung hình vuông kích thước $(a, a)$ với $a = \min(h, w)$ bao quanh tâm rác $(c_x, c_y)$, có giới hạn trượt trong biên ảnh gốc ($0 \le \text{crop}_x \le w - a$, $0 \le \text{crop}_y \le h - a$).
   - *Cơ chế Fallback:* Trong trường hợp không tách được nền hoặc không cài đặt `rembg`, hệ thống tự động cắt khung vuông căn chính giữa tâm ảnh gốc $(w - a)//2, (h - a)//2$ để giữ nguyên tỷ lệ khung hình 1:1, tuyệt đối không làm bẹp hay méo mó hình dạng vật thể rác.
3. **Bước 3: Tái định cỡ quang học chống răng cưa (Optical Area Resampling):**
   - Định cỡ lại ảnh vuông đã cắt về kích thước chuẩn của mô hình: $\text{IMG\_SIZE} = (320, 320)$.
   - Sử dụng thuật toán lấy mẫu vùng `tf.image.ResizeMethod.AREA` (kèm `antialias=True`) hoặc `cv2.INTER_AREA`.
   - *Ưu thế kỹ thuật:* So với Bilinear/Nearest thông thường, thuật toán Area Resampling triệt tiêu hiện tượng răng cưa méo mó và giữ trọn vẹn kết cấu bề mặt vật liệu rác (độ bóng của vỏ chai nhựa, nếp nhăn của giấy, ánh kim của lon nhôm).
4. **Bước 4: Chuẩn hóa phân phối điểm ảnh (ConvNeXt Normalization):**
   - Chuyển tensor hình ảnh sang dạng số thực `float32`.
   - Chuẩn hóa kênh màu qua hàm `tf.keras.applications.convnext.preprocess_input(img)` chuẩn xác theo phân phối ImageNet của kiến trúc ConvNeXt.
5. **Bước 5: Suy luận Đa góc nhìn (5-View TTA Inference) & Tổng hợp Softmax:**
   - Theo Cell 9 của notebook, để tăng cường độ ổn định và giảm thiểu phương sai dự đoán, hệ thống sinh ra 5 biến thể hình học cho ảnh:
     * *View 1:* Ảnh gốc đã chuẩn hóa.
     * *View 2:* Lật ngang (`flip_left_right`).
     * *View 3:* Xoay $90^\circ$ theo chiều kim đồng hồ (`rot90, k=1`).
     * *View 4:* Xoay $270^\circ$ (`rot90, k=3`).
     * *View 5:* Cắt trung tâm 90% (Center Crop 90%) rồi tái định cỡ Area về $320 \times 320$.
   - Trích xuất Logits từ tầng `CosineDense(scale=20.0)` và tính xác suất Softmax cho từng View: $P^{(v)} = \text{softmax}(\text{logits}^{(v)})$.
   - Tổng hợp xác suất Softmax Ensemble trung bình: $P = \frac{1}{5}\sum_{v=1}^5 P^{(v)}$ (Backend cũng hỗ trợ chế độ Single-View chạy nhanh khi cần độ trễ cực thấp < 50ms).
6. **Bước 6: Hệ thống kiểm soát an toàn 2 Chốt & Quy trình Tái thẩm định thích ứng 3 Cấp độ (3-Tier Adaptive Safety Filter):**
   *(Kế thừa nguyên bản thiết kế thuật toán an toàn tại Mục 7 trong `docs/Luong_hoat_dong.md`, Cell 10 và xuất cấu hình động tại Cell 13 trong notebook `kltn-convnext-tiny.ipynb`)*
   - **Cơ chế nạp động từ file cấu hình (Zero Hardcoding):**
     * Toàn bộ giá trị ngưỡng ($\tau_{conf}$ từng lớp, $\tau_{margin}$ chung, hệ số $k_1, k_2$, trọng số bù trừ $W_{conf}, W_{margin}$, các ngưỡng sàn và chuỗi gợi ý tiếng Việt) được nạp trực tiếp từ file `safety_thresholds.json` khi Backend khởi động.
     * Khi cần tinh chỉnh ngưỡng an toàn hoặc thêm nhãn mới, hệ thống chỉ cần đọc file JSON này mà không phải sửa hay build lại mã nguồn Python.
   - **Xác định các chỉ số suy luận cốt lõi:**
     * Độ tự tin Top-1: $Conf = \max_c P(c)$.
     * Khoảng cách biên phân biệt Top 1 - Top 2: $Margin = Conf_{Top1} - Conf_{Top2}$.
     * Độ ổn định đồng thuận 5 góc nhìn TTA (Consensus Stability): $TTA\_Stability = \frac{1}{5}\sum_{v=1}^5 \mathbb{I}(\text{pred}^{(v)} == \text{pred}_{final})$.
   - **Khóa bộ ngưỡng an toàn thống kê trên tập Validation ($\mu - k\sigma$):**
     * *Chốt 1 ($\tau_{conf}$ - Thích ứng riêng từng lớp):* $\tau_{conf}(c) = \mu_c - k_1(c)\sigma_c$ (ví dụ: các lớp Glass, Metal, Paper, Plastic có ngưỡng tự tin riêng được hiệu chuẩn trên tập validation).
     * *Chốt 2 ($\tau_{margin}$ - Chung toàn hệ thống):* $\tau_{margin} = \mu_m - k_2\sigma_m$ (khống chế trường hợp mô hình phân vân giữa 2 lớp rác tương đồng).
   - **Chuẩn hóa điểm an toàn thành phần & Điểm an toàn kết hợp (Composite Safety Score):**
     $$s_{conf} = \frac{Conf}{\tau_{conf}(c)}, \quad s_{margin} = \frac{Margin}{\tau_{margin}}$$
     $$S_{composite} = 0.50 \cdot s_{conf} + 0.50 \cdot s_{margin}$$
   - **Vận hành quy trình tái thẩm định thích ứng 3 cấp độ cho mẫu có độ bất định:**
     * **Cấp 1 — Bộ lọc chuẩn kép cơ sở (Hard Standard Gates):**
       $$\text{Điều kiện:} \quad (Conf \ge \tau_{conf}(c)) \quad \text{VÀ} \quad (Margin \ge \tau_{margin})$$
       $\rightarrow$ **Quyết định:** Luồng `Tự động` (`Tu_Dong_Gap`), Trạng thái `Thành công`. Lý do: *"Đạt chuẩn cơ sở 5-View TTA (Chốt 1: s_conf | Chốt 2: s_margin)"*.
     * **Cấp 2 — Cơ chế cứu nguy bù trừ an toàn (Composite Safety Rescue):**
       Áp dụng cho các mẫu trượt Cấp 1 do một chốt hơi thấp nhưng chốt còn lại áp đảo (ví dụ $Conf = 99\%$ nhưng $Margin$ hơi hẹp):
       $$\text{Điều kiện:} \quad (S_{composite} \ge 1.0) \quad \text{VÀ} \quad (Conf \ge 70\%)$$
       $\rightarrow$ **Quyết định:** Luồng `Tự động` (`Tu_Dong_Gap`), Trạng thái `Thành công`. Lý do: *"Cứu nguy bù trừ an toàn (Điểm: S_composite >= 100%)"*.
     * **Cấp 3 — Cửa phụ bảo lãnh đồng thuận đa góc nhìn (TTA Consensus Rescue):**
       Áp dụng cho mẫu trượt Cấp 2 nhưng nhận được sự bảo lãnh an toàn tuyệt đối từ cả 5 biến thể hình học TTA:
       $$\text{Điều kiện:} \quad (S_{composite} \ge 0.90) \quad \text{VÀ} \quad (TTA\_Stability \ge 0.999) \quad \text{VÀ} \quad (Conf \ge 65\%)$$
       $\rightarrow$ **Quyết định:** Luồng `Tự động` (`Tu_Dong_Gap`), Trạng thái `Thành công`. Lý do: *"Cứu nguy bảo lãnh TTA 100% (Điểm: S_composite >= 90% | Đồng thuận: 100%)"*.
     * **Phân luồng thủ công (Manual Fallback):**
       Mẫu không thỏa mãn bất kỳ tiêu chí nào trong 3 cấp trên:
       $\rightarrow$ **Quyết định:** Luồng `Thủ công` (`Chuyen_Khay_Thu_Cong`), Trạng thái `Cần kiểm tra`. Ghi rõ lý do vi phạm chi tiết từng chốt (ví dụ: *"Chốt 1: Tự tin thấp lớp Nhựa (64.2% < 85.0%) | Chốt 2: Biên Margin hẹp (12.1% < 45.0%)"*).
7. **Bước 7: Giải thích mô hình bằng XAI (Grad-CAM & Spatial Energy Map - Cell 12):**
   - Trích xuất ma trận đặc trưng không gian $F \in \mathbb{R}^{10 \times 10 \times C}$ từ tầng cuối trước pooling (`convnext_tiny_stage_3_block_2_identity`).
   - Tính toán bản đồ năng lượng kích hoạt: $\text{Energy}_{i,j} = \sqrt{\frac{1}{C}\sum_k (F_{i,j}^k)^2}$.
   - Tính toán Grad-CAM cho lớp dự đoán $c$: Sử dụng `tf.GradientTape()` tính đạo hàm $\alpha_k^c = \frac{1}{Z}\sum_i \sum_j \frac{\partial y^c}{\partial F_{i,j}^k}$ và tổng hợp $L_{\text{Grad-CAM}}^c = \text{ReLU}\left(\sum_k \alpha_k^c F^k\right)$.
   - Phóng to ma trận $10 \times 10$ lên $320 \times 320$ (Bicubic), áp bảng màu nhiệt `cv2.COLORMAP_JET` và phủ đè lên ảnh gốc với tỷ lệ $\alpha = 0.48$.
   - Tải ảnh kết quả phủ nhiệt lên Cloudinary (hoặc R2) để người dùng có thể xem giải thích trực quan: mô hình dựa vào bộ phận nào (thân chai, nắp chai, nhãn mác...) để đưa ra nhãn rác.

#### Cấu trúc JSON Response bắt buộc của API `/predict/single`:
```json
{
  "id": "c1f7b0a8-5d23-4e89-a6f1-3d7120a4b889",
  "file_name": "plastic_bottle_01.jpg",
  "image_url": "https://res.cloudinary.com/dxyzt123/image/upload/v1794820000/trash_classification/uploads/single/2026/11/16/c1f7b0a8_plastic_bottle_01.jpg",
  "xai_overlay_url": "https://res.cloudinary.com/dxyzt123/image/upload/v1794820000/trash_classification/uploads/xai/2026/11/16/c1f7b0a8_gradcam_overlay.jpg",
  "waste_type": "Nhựa",
  "confidence": 96.5,
  "margin": 91.8,
  "checkpoint_1": 94.2,
  "checkpoint_2": 91.8,
  "composite_score": 102.4,
  "tta_stability": 100.0,
  "decision_tier": "Tier 1: Đạt chuẩn cơ sở",
  "pipeline_type": "Tự động",
  "status": "Thành công",
  "reason": "Đạt chuẩn cơ sở 5-View TTA (Chốt 1: 1.02x | Chốt 2: 1.00x)",
  "suggestion": "Thu gom vào thùng rác tái chế.",
  "created_at": "2026-11-16T08:32:15.000Z"
}
```

---

### 3.3. Yêu cầu Database & Cloud Storage

| # | Yêu cầu | Chi tiết kỹ thuật | Mức độ |
|---|---|---|---|
| **D1** | Khởi tạo Cloudinary Storage (hoặc R2) | Đăng ký Cloudinary miễn phí 25GB bằng Google trong 10 giây (không cần thẻ). Lấy `CLOUDINARY_CLOUD_NAME`, `CLOUDINARY_API_KEY`, `CLOUDINARY_API_SECRET` để cấp phát CDN HTTPS vĩnh viễn. (Hỗ trợ dự phòng Cloudflare R2). | Bắt buộc |
| **D2** | Module kết nối Cloud Storage (`cloudinary_storage.py` / `r2_storage.py`) | Sử dụng SDK `cloudinary` upload file ảnh rác và ảnh nhiệt XAI vào thư mục `trash_classification/uploads/single|batch|xai/YYYY/MM/DD/`, trả về URL công khai load tốc độ cao. | Bắt buộc |
| **D3** | Khởi tạo Supabase Database (hoặc MongoDB Atlas) | Tạo Project `trash-classification` trên Supabase (khu vực Singapore), gói Free 100% không cần thẻ tín dụng. Cấu hình bảng PostgreSQL qua SQL Editor. (Hỗ trợ dự phòng MongoDB Atlas). | Bắt buộc |
| **D4** | Thiết kế Bảng / Collection `prediction_logs` | Lưu trữ kết quả phân loại với các trường: `id` (UUID), `file_name`, `image_url` (từ Cloudinary/R2), `xai_overlay_url` (ảnh phủ nhiệt Grad-CAM), `waste_type`, `confidence`, `margin`, `checkpoint_1`, `checkpoint_2`, `composite_score`, `tta_stability`, `decision_tier`, `reason`, `pipeline_type`, `status`, `suggestion`, `created_at` và `metadata`. | Bắt buộc |
| **D5** | Quản lý phiên xử lý nhiều ảnh | Quản lý thông tin phiên xử lý nhiều ảnh gồm: `batch_id`, `total_images`, `processed_images`, `pending_images`, `completion_rate`, `status`, `created_at`. | Nâng cao |
| **D6** | Indexing chiến thuật trên Database | Đánh chỉ mục hiệu năng cao (B-Tree trên Supabase PostgreSQL / Index trên MongoDB):<br/>- `created_at desc` (Sắp xếp lịch sử mới nhất)<br/>- `waste_type` (Lọc theo loại rác)<br/>- `pipeline_type` (Lọc theo luồng Tự động / Thủ công)<br/>- `file_name` (Tìm kiếm nhanh theo tên file). | Bắt buộc |
| **D7** | Xử lý chịu lỗi kết nối (Fault Tolerance) | Triển khai cơ chế retry và graceful degradation: nếu Supabase hoặc Cloudinary mất kết nối tạm thời, API trả mã lỗi rõ ràng mà không làm gián đoạn toàn bộ tiến trình ứng dụng. | Nâng cao |

#### Cấu trúc Bản ghi dữ liệu mẫu (`prediction_logs`):
```json
{
  "id": "c1f7b0a8-5d23-4e89-a6f1-3d7120a4b889",
  "file_name": "plastic_bottle_01.jpg",
  "image_url": "https://res.cloudinary.com/dxyzt123/image/upload/v1794820000/trash_classification/uploads/single/2026/11/16/c1f7b0a8_plastic_bottle_01.jpg",
  "xai_overlay_url": "https://res.cloudinary.com/dxyzt123/image/upload/v1794820000/trash_classification/uploads/xai/2026/11/16/c1f7b0a8_gradcam_overlay.jpg",
  "waste_type": "Nhựa",
  "confidence": 96.5,
  "margin": 91.8,
  "checkpoint_1": 94.2,
  "checkpoint_2": 91.8,
  "composite_score": 102.4,
  "tta_stability": 100.0,
  "decision_tier": "Tier 1: Đạt chuẩn cơ sở",
  "pipeline_type": "Tự động",
  "status": "Thành công",
  "reason": "Đạt chuẩn cơ sở 5-View TTA (Chốt 1: 1.02x | Chốt 2: 1.00x)",
  "suggestion": "Thu gom vào thùng rác tái chế.",
  "created_at": "2026-11-16T08:32:15.000Z",
  "metadata": {
    "file_size": 245100,
    "mime_type": "image/jpeg",
    "inference_time_ms": 38.5,
    "model_version": "convnext_tiny_v2"
  }
}
```

---

### 3.4. Yêu cầu Frontend

| # | Yêu cầu | Chi tiết kỹ thuật & Giao diện tham chiếu | Mức độ |
|---|---|---|---|
| **F1** | Sidebar điều hướng cố định | Bố trí thanh Sidebar nền xanh navy đậm cố định bên trái, logo thùng rác + text "Phân loại rác", menu gồm 2 mục: **Phân loại** (Icon layers) và **Lịch sử** (Icon đồng hồ). Hiển thị rõ mục đang được chọn. | Bắt buộc |
| **F2** | Màn hình Phân loại 1 ảnh (Tab "Một ảnh") | **Giao diện tham chiếu:** [Giao diện/Phân loại 1 ảnh.png](./Giao%20diện/Phân%20loại%201%20ảnh.png)<br/>- Khối bên trái: Vùng kéo thả ảnh / chọn tệp, xem trước ảnh đã chọn + tên file, nút `[▶ Bắt đầu dự đoán]` và nút `[↺ Làm mới]`.<br/>- Khối bên phải: Card Loại rác kèm badge trạng thái (`✓ Kết quả hợp lệ` hoặc `⚠ Cần kiểm tra`), 3 thanh progress bar (`Độ tin cậy %`, `Chốt 1 %`, `Chốt 2 %`), khung Gợi ý xử lý và **Nút chuyển đổi xem ảnh giải thích XAI Grad-CAM Overlay** (`[Ảnh gốc]` / `[Bản đồ nhiệt Grad-CAM]`). | Bắt buộc |
| **F3** | Màn hình Phân loại thư mục / nhiều ảnh (Tab "Nhiều ảnh") | **Giao diện tham chiếu:** [Giao diện/Phân loại thư mục nhiều ảnh.png](./Giao%20diện/Phân%20loại%20thư%20mục%20nhiều%20ảnh.png)<br/>- Khối trên trái: Kéo thả nhiều ảnh hoặc thư mục, 2 nút `[Chọn nhiều ảnh]` và `[Chọn thư mục]`.<br/>- Khối trên phải: 4 thẻ thống kê tiến độ (*Tổng số ảnh*, *Đã xử lý*, *Đang chờ*, *Tỷ lệ hoàn thành %*), thanh Progress Bar tổng thể và nút `[▶ Bắt đầu xử lý]`.<br/>- Khối dưới: Bảng kết quả đã xử lý (Thumbnail + Tên ảnh, Loại rác, Độ tin cậy, Chốt 1, Chốt 2, Trạng thái), thanh tìm kiếm tên ảnh, bộ lọc theo loại rác; hỗ trợ nhấn vào dòng để xem chi tiết. | Bắt buộc |
| **F4** | Màn hình Lịch sử phân loại (Tổng quan) | **Giao diện tham chiếu:** [Giao diện/Lịch sử trước khi chọn 1 dòng.png](./Giao%20diện/Lịch%20sử%20trước%20khi%20chọn%201%20dòng.png)<br/>- Thanh bộ lọc: Ô tìm kiếm tên file, dropdown Loại rác, dropdown Luồng xử lý (`Tất cả`/`Tự động`/`Thủ công`), dropdown Thời gian và nút `[📥 Xuất lịch sử]`.<br/>- Bảng dữ liệu: STT, Tên file, Loại rác, Độ tin cậy, Luồng xử lý (Badge màu), Thời gian dự đoán.<br/>- Phân trang: Hiển thị số lượng bản ghi và các nút chuyển trang `[<] [1] [2] ... [>]`. | Bắt buộc |
| **F5** | Màn hình Lịch sử hiển thị chi tiết 1 dòng (Split View) | **Giao diện tham chiếu:** [Giao diện/Lịch sử hiển thị thông tin chi tiết 1 dòng.png](./Giao%20diện/Lịch%20sử%20hiển%20thị%20thông%20tin%20chi%20tiết%201%20dòng.png)<br/>- Khi người dùng click chọn 1 dòng trong bảng lịch sử: Giao diện chuyển sang dạng Split View.<br/>- Cột trái: Bảng lịch sử co lại, dòng chọn được highlight.<br/>- Cột phải: Panel "Chi tiết dự đoán" hiển thị ảnh kích thước lớn load trực tiếp từ Cloudinary / R2 (kèm nút toggle xem ảnh phủ nhiệt XAI Grad-CAM), tên file, badge loại rác, độ tin cậy %, badge luồng xử lý và ngày giờ dự đoán. | Bắt buộc |
| **F6** | Trạng thái tải (Loading state) & Thanh tiến trình | Hiển thị skeleton/spinner khi đang chờ API dự đoán 1 ảnh; cập nhật thanh tiến trình % theo thời gian thực khi xử lý batch nhiều ảnh. | Bắt buộc |
| **F7** | Bắt lỗi & Thông báo (Toast Notification) | Thông báo lỗi thân thiện khi API quá tải, mất mạng hoặc file upload sai định dạng; thông báo thành công khi xuất lịch sử hoàn tất. | Bắt buộc |
| **F8** | Thiết kế Responsive | Tương thích và hiển thị tốt trên các độ phân giải màn hình từ Desktop đến Laptop/Tablet. | Bắt buộc |
| **F9** | Trực quan hóa XAI Heatmap (Grad-CAM Viewer) | Hỗ trợ hiển thị bản đồ nhiệt màu JET trực quan minh bạch hóa đặc trưng nhận diện của mô hình AI, giúp người vận hành biết được mô hình dựa vào đâu để ra quyết định phân loại rác. | Nâng cao |
| **F10**| Đèn báo trạng thái Server & Pre-warming Ping | Khi mở web, Frontend tự động gửi ngầm request `GET /health` để đánh thức Backend dự phòng và hiển thị đèn trạng thái trực quan trên Sidebar: 🟢 *Máy chủ AI sẵn sàng*, 🟡 *Đang kết nối...*, 🔴 *Mất kết nối*. | Nâng cao |

---

### 3.5. Yêu cầu Triển khai (Deployment)

| # | Yêu cầu | Chi tiết kỹ thuật | Mức độ |
|---|---|---|---|
| **P1** | Backend deploy trên Render.com từ Monorepo | Kết nối 1 repository GitHub duy nhất, thiết lập **Root Directory: `backend`**, build Native Python 3 với `pip` và khởi chạy qua `uvicorn`. | Bắt buộc |
| **P2** | Frontend deploy trên Vercel từ Monorepo | Kết nối cùng 1 repository GitHub, thiết lập **Root Directory: `frontend`**, build tự động Next.js 14 với domain production. | Bắt buộc |
| **P3** | Cloudinary Image Storage đã kích hoạt | Cloudinary credentials cấu hình chuẩn xác, upload ảnh gốc và ảnh Grad-CAM thành công, link CDN HTTPS hiển thị tức thì. | Bắt buộc |
| **P4** | Database Supabase (PostgreSQL) đã kích hoạt | Bảng `prediction_logs` tạo thành công với chỉ mục tối ưu, kết nối mượt qua `supabase-py` SDK. | Bắt buộc |
| **P5** | Cấu hình Biến môi trường (.env) | Thiết lập đầy đủ biến môi trường trên Vercel (`NEXT_PUBLIC_API_URL`) và Render (`SUPABASE_URL`, `SUPABASE_KEY`, `CLOUDINARY_...`). | Bắt buộc |
| **P6** | Thiết lập CORS Middleware | Backend cho phép domain frontend Vercel gọi API mà không gặp lỗi bảo mật Cross-Origin. | Bắt buộc |
| **P7** | Cơ chế UptimeRobot kép chống ngủ đông | Thiết lập 2 monitor trên UptimeRobot: (1) Ping Render Backend `/api/v1/health` mỗi 10 phút chống Cold Start; (2) Ping Supabase REST API chống tạm dừng dự án sau 7 ngày. | Nâng cao |

---

## 4. Sản phẩm nộp bài (Mô hình Monorepo)

### 4.1. Source code (1 GitHub Repository duy nhất)
Dự án áp dụng mô hình **Monorepo** chuẩn hóa với **1 GitHub repository duy nhất** (ví dụ: `trash-classification-system`):
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
- **Frontend URL (Vercel):** `https://trash-classification-web.vercel.app`
- **Backend API URL (Render):** `https://trash-classification-api.onrender.com`
- **Swagger UI (Interactive API Docs):** `https://trash-classification-api.onrender.com/docs`

### 4.3. Kịch bản Demo thực nghiệm
1. **Demo Phân loại 1 ảnh:** Tải 1 ảnh rác thải $\rightarrow$ Xem kết quả hiển thị gồm Loại rác, 3 thanh tiến trình (% tin cậy, Chốt 1, Chốt 2), badge trạng thái và gợi ý xử lý.
2. **Demo Phân loại theo thư mục:** Chọn một thư mục nhiều ảnh rác $\rightarrow$ Quan sát thanh tiến trình chạy và danh sách ảnh được xử lý đổ vào bảng dữ liệu.
3. **Demo Tra cứu Lịch sử:** Lọc dữ liệu theo loại rác hoặc luồng xử lý $\rightarrow$ Click vào 1 dòng để xem panel chi tiết bên phải (hình ảnh load từ Cloudinary / R2) $\rightarrow$ Nhấn nút *Xuất lịch sử* để tải file CSV.

---

## 5. Tiêu chí chấm điểm & Nghiệm thu (100 Điểm)

| Hạng mục | Điểm | Tiêu chí chi tiết |
|:---|:---:|:---|
| **1. ML Model & Hệ thống 2 Chốt & XAI** | **20** | |
| - Nạp model ConvNeXt-Tiny & Tiền xử lý ảnh ($320 \times 320$ AREA) | 6 | Model chạy suy luận ổn định, output xác suất Softmax chuẩn xác |
| - Module an toàn 2 Chốt & Quy trình tái thẩm định thích ứng 3 Cấp độ | 7 | Đạt chuẩn thiết kế Cell 10 notebook: tính đúng 2 chốt an toàn ($\tau_{conf}$, $\tau_{margin}$), điểm bù trừ $S_{composite}$, bảo lãnh TTA và phân luồng chuẩn xác theo 3 cấp độ (Hard Gates, Composite Rescue, TTA Consensus Rescue) |
| - Gợi ý hành động xử lý rác tương ứng loại rác | 3 | Gợi ý đúng loại thùng rác (tái chế, hữu cơ, vô cơ...) |
| - Trực quan hóa giải thích XAI (Grad-CAM & Spatial Energy) | 4 | Trích xuất thành công bản đồ nhiệt JET Overlay minh bạch hóa nhận diện |
| **2. Backend API (FastAPI)** | **25** | |
| - Endpoint `/predict/single` và `/predict/batch` | 10 | Nhận ảnh đơn & danh sách ảnh, xử lý trả kết quả đầy đủ 6 trường cốt lõi |
| - Endpoint `/history`, `/history/{id}` và `/history/export` | 8 | Lấy lịch sử có phân trang, xem chi tiết và xuất file CSV thành công |
| - Pydantic Validation & Health Check `/health` | 4 | Validate định dạng ảnh chặt chẽ, báo trạng thái hệ thống |
| - CORS & Quản lý Exception tập trung | 3 | Kết nối an toàn, format lỗi chuẩn HTTP |
| **3. Database & Cloud Storage** | **15** | |
| - Tích hợp Cloudinary (hoặc R2) lưu trữ hình ảnh (ảnh gốc + ảnh XAI) | 8 | Ảnh upload được đẩy lên Cloudinary CDN, trả về link công khai load nhanh |
| - Tích hợp Supabase (hoặc MongoDB Atlas) lưu trữ dữ liệu lịch sử | 7 | Lưu đầy đủ các trường yêu cầu, index chạy mượt khi tìm kiếm/phân trang |
| **4. Frontend (Next.js 14+)** | **25** | |
| - Màn hình Phân loại 1 ảnh (Tab "Một ảnh") | 6 | Khớp chính xác thiết kế: Dropzone, Preview, Card kết quả, 3 Progress bar |
| - Màn hình Phân loại thư mục (Tab "Nhiều ảnh") | 6 | Khớp chính xác: 4 thẻ tiến độ, progress bar, bảng kết quả có tìm kiếm & lọc |
| - Màn hình Lịch sử & Split View xem chi tiết | 7 | Khớp chính xác: Filter bar, bảng phân trang, click dòng mở panel ảnh lớn |
| - Trực quan hóa XAI Heatmap Viewer | 3 | Nút chuyển đổi xem ảnh gốc và ảnh Grad-CAM Overlay trực quan |
| - UI/UX, Sidebar cố định & Responsive | 3 | Giao diện đồng bộ tông xanh navy, hiệu ứng mượt mà |
| **5. Triển khai Cloud & Code Quality** | **15** | |
| - Triển khai Production live (Vercel + Render + Cloudinary + Supabase) | 8 | Toàn bộ luồng hoạt động thông suốt trên internet |
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
│ **Giai đoạn 1**     │ • Tạo tài khoản Cloudinary & Project     │ • Module Cloudinary & │
│ *(Ngày 1 - 2)*      │   Supabase (kèm bảng SQL).               │   Supabase Adapter    │
│                     │ • Đóng gói hàm suy luận ConvNeXt-Tiny.   │ • Module Model Loader │
│                     │ • Viết thuật toán 2 Chốt chặn & Quy trình│ • Module An toàn      │
│                     │   tái thẩm định thích ứng 3 Cấp độ.      │   3 Cấp độ Thích ứng  │
├─────────────────────┼──────────────────────────────────────────┼───────────────────────┤
│ **Giai đoạn 2**     │ • Khởi tạo FastAPI App, Pydantic schemas.│ • Hoàn thiện Backend  │
│ *(Ngày 3 - 4)*      │ • Xây dựng API `/predict/single` và      │   FastAPI với đầy đủ  │
│                     │   `/predict/batch`.                      │   Swagger UI `/docs`  │
│                     │ • Xây dựng API `/history` có phân trang, │                       │
│                     │   lọc và export file CSV.                │                       │
├─────────────────────┼──────────────────────────────────────────┼───────────────────────┤
│ **Giai đoạn 3**     │ • Khởi tạo Next.js 14, Tailwind CSS.     │ • Giao diện hoàn chỉnh│
│ *(Ngày 5 - 7)*      │ • Dựng Sidebar xanh navy cố định.        │   khớp 4 ảnh mẫu      │
│                     │ • Dựng Tab 1 ảnh & Tab Nhiều ảnh.        │ • Kết nối Axios API   │
│                     │ • Dựng Trang Lịch sử & Split View xem    │                       │
│                     │   chi tiết kết quả ảnh từ Cloudinary.    │                       │
├─────────────────────┼──────────────────────────────────────────┼───────────────────────┤
│ **Giai đoạn 4**     │ • Tích hợp End-to-End Frontend - Backend.│ • Hệ thống Production │
│ *(Ngày 8 - 9)*      │ • Triển khai Vercel, Render, Cloudinary, │   Vercel & Render &   │
│                     │   Supabase + Thiết lập UptimeRobot kép.  │   Supabase 24/7       │
│                     │ • Kiểm thử tải, đo độ trễ và nghiệm thu. │ • Báo cáo nghiệm thu  │
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
│                             │(Root: fe) │       │(Root: be) │                          │
│                             └─────┬─────┘       └─────┬─────┘                          │
│                                   │                   │                                │
│                     NEXT_PUBLIC_API_URL               │                                │
│                                   │                   │                                │
│                                   ▼                   ▼                                │
│                              Gọi REST API     ┌───────────────┐                        │
│                              (Multipart POST) │  Cloudinary   │                        │
│                                       │       │ (hoặc R2)     │ (Upload & Link ảnh CDN)│
│                                       │       └───────────────┘                        │
│                                       │               ▲                                │
│                                       ▼               │                                │
│                               ┌───────────────┐       │                                │
│                               │   Supabase    │◀──────┘                                │
│                               │(hoặc MongoDB) │                                        │
│                               │  (Lưu DB Log) │                                        │
│                               └───────────────┘                                        │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

### 7.1. Cấu hình Supabase & Lấy SUPABASE_URL + SUPABASE_KEY (Kèm SQL tạo bảng)

Supabase cung cấp cơ sở dữ liệu quan hệ PostgreSQL trên đám mây, gói Free hoàn toàn miễn phí không đòi hỏi thẻ tín dụng.

#### Bước 1: Tạo tài khoản & Project trên Supabase
1. Truy cập [https://supabase.com/](https://supabase.com/) $\rightarrow$ Chọn **Start your project** $\rightarrow$ Đăng nhập bằng GitHub hoặc Google.
2. Nhấn nút **New Project**:
   - **Organization:** Chọn tổ chức mặc định của bạn.
   - **Name:** Đặt tên `trash-classification`.
   - **Database Password:** Nhập mật khẩu mạnh (hãy lưu lại mật khẩu này).
   - **Region:** Chọn `Southeast Asia (Singapore)` để tối ưu tốc độ kết nối về Việt Nam.
3. Nhấn **Create new project** và chờ khoảng 1-2 phút để cụm database khởi tạo hoàn tất.

#### Bước 2: Chạy câu lệnh SQL tạo bảng `prediction_logs`
1. Trong menu bên trái của Supabase Dashboard, chọn biểu tượng **SQL Editor**.
2. Nhấn **New query** và dán toàn bộ đoạn mã SQL sau:
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
       created_at timestamptz default timezone('utc'::text, now()),
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
   - **anon / public key:** Chuỗi JWT dài $\rightarrow$ Điền vào `SUPABASE_KEY`.

---

### 7.2. Cấu hình ImageKit.io & Lấy API Credentials (IMAGEKIT_PUBLIC_KEY, PRIVATE_KEY, URL_ENDPOINT)

ImageKit.io cung cấp giải pháp lưu trữ hình ảnh đám mây chuyên nghiệp, miễn phí 20GB trọn đời, đăng ký bằng Google trong 10 giây và không yêu cầu thẻ tín dụng.

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
3. Lưu 3 thông số này vào file `backend/.env`. ImageKit cấp phát URL ảnh công khai CDN vĩnh viễn dạng:
   ```text
   https://ik.imagekit.io/<ID>/uploads/...
   ```
   Hoàn toàn không cần kích hoạt domain phụ hay trả phí.

---

### 7.3. Cấu hình triển khai Backend FastAPI trên Render (từ Monorepo)

Render hỗ trợ triển khai trực tiếp từ một thư mục con trong Monorepo thông qua cấu hình **Root Directory**.

#### Bước 1: Tạo Web Service mới trên Render
1. Truy cập [https://dashboard.render.com/](https://dashboard.render.com/) $\rightarrow$ Đăng nhập bằng tài khoản GitHub chứa mã nguồn dự án.
2. Nhấn nút **New +** ở góc trên cùng $\rightarrow$ Chọn **Web Service**.
3. Chọn **Build and deploy from a Git repository** $\rightarrow$ Nhấn Next.
4. Chọn repository GitHub duy nhất của dự án (`trash-classification-system`).

#### Bước 2: Cài đặt Monorepo & Build Settings
Cấu hình các trường thông tin chính xác như sau:
- **Name:** `trash-classification-api`
- **Region:** `Singapore (Southeast Asia)`
- **Branch:** `main` (hoặc nhánh bạn đang push code)
- **Root Directory:** Nhập chính xác: **`backend`** *(Rất quan trọng: Chỉ thị cho Render chỉ đọc và build thư mục `backend/`)*.
- **Runtime:** `Python 3` (Môi trường Native Python thuần)
- **Build Command:** `pip install -r requirements.txt`
- **Start Command:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- **Instance Type:** Chọn gói phù hợp (Lưu ý: Mô hình ConvNeXt-Tiny cần tối thiểu 1.5GB – 2GB RAM để nạp weights ổn định).

#### Bước 3: Thêm Biến môi trường (Environment Variables) trên Render
Chuyển sang tab **Environment** trên Render và thêm các biến sau:

| Key | Giá trị mẫu / Hướng dẫn |
|:---|:---|
| `PORT` | `8000` |
| `ENVIRONMENT` | `production` |
| `SUPABASE_URL` | URL Supabase lấy ở Bước 7.1 (`https://xxx.supabase.co`) |
| `SUPABASE_KEY` | Khóa `anon / public` JWT lấy ở Bước 7.1 |
| `IMAGEKIT_PUBLIC_KEY` | Public Key lấy ở Bước 7.2 |
| `IMAGEKIT_PRIVATE_KEY` | Private Key lấy ở Bước 7.2 |
| `IMAGEKIT_URL_ENDPOINT` | URL Endpoint lấy ở Bước 7.2 (`https://ik.imagekit.io/...`) |
| `MODEL_PATH` | `checkpoints/best_trashnet_convnext_retrained.keras` |
| `CORS_ORIGINS` | `["http://localhost:3000"]` *(sẽ bổ sung domain Vercel sau khi tạo Vercel)* |
| *(Tùy chọn) `CLOUDINARY_*`* | *(Nếu dùng Cloudinary)* Cấu hình `CLOUDINARY_CLOUD_NAME`, `API_KEY`, `API_SECRET` |
| *(Tùy chọn) `MONGODB_URI`* | *(Nếu dùng MongoDB Atlas)* `mongodb+srv://...` |
| *(Tùy chọn) `R2_*`* | *(Nếu dùng Cloudflare R2)* Cấu hình `R2_ACCOUNT_ID`, `R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY` |

#### Bước 4: Hướng dẫn chi tiết cách tìm, lấy và cấu hình các Đường dẫn (URLs) từ Render Dashboard

Sau khi Render tạo Web Service thành công, giao diện Dashboard của Render sẽ cung cấp các đường dẫn quan trọng cần thiết để vận hành, giám sát và kết nối Backend:

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                              RENDER DASHBOARD GIAO DIỆN                                │
│                                                                                        │
│  [Web Service] trash-classification-api  ● Live                                        │
│  🔗 https://trash-classification-api.onrender.com   [📋 Copy URL] ◀── (1) Public URL  │
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
   - **Vị trí tìm trên giao diện:** Nằm ở góc trên bên trái của trang Web Service Dashboard, ngay phía dưới tên dịch vụ `trash-classification-api` (hiển thị màu tím nhạt/xanh kèm biểu tượng link).
   - **Cách lấy:** Nhấp trực tiếp vào biểu tượng **Copy** cạnh link hoặc click chuột phải chọn *Copy link address*.
   - **Định dạng đường dẫn:**
     ```text
     https://trash-classification-api.onrender.com
     ```
   - **Mục đích sử dụng:**
     - Dùng làm URL gốc (Base URL) cho toàn bộ API backend.
     - Cung cấp cho Frontend trên Vercel: Cấu hình biến môi trường `NEXT_PUBLIC_API_URL = https://trash-classification-api.onrender.com/api/v1`.
     - Dùng cho Postman / cURL để kiểm thử API từ bên ngoài.

2. **Đường dẫn Swagger UI & ReDoc (Tài liệu API tương tác):**
   - **Cách ghép link:** Lấy Web Service URL ở trên và ghép thêm đuôi `/docs` hoặc `/redoc`:
     - **Swagger UI:** `https://trash-classification-api.onrender.com/docs`
     - **ReDoc:** `https://trash-classification-api.onrender.com/redoc`
   - **Mục đích sử dụng:** Mở trực tiếp trên trình duyệt để kiểm tra danh sách API, thử nghiệm upload file ảnh vào endpoint `POST /predict/single` và xem kết quả trả về ngay lập tức.

3. **Cấu hình đường dẫn Health Check Path trên Render:**
   - **Vị trí cài đặt:** Vào tab **Settings** của Web Service $\rightarrow$ Cuộn xuống mục **Health Check Path**.
   - **Đường dẫn cần nhập:** Nhập chính xác:
     ```text
     /api/v1/health
     ```
   - **Mục đích sử dụng:** Render sẽ gửi request HTTP GET định kỳ tới đường dẫn này. Nếu Backend trả về status `200 OK`, Render xác nhận dịch vụ hoạt động khỏe mạnh (Healthy). Nếu Backend gặp lỗi hoặc quá tải RAM, Render sẽ tự động khởi động lại instance để khôi phục dịch vụ (Zero-Downtime Recovery).

4. **Đường dẫn Deploy Hook (Kích hoạt Build tự động từ xa):**
   - **Vị trí lấy:** Vào tab **Settings** $\rightarrow$ Cuộn xuống mục **Deploy Hooks** $\rightarrow$ Nhấn nút **Add Deploy Hook**.
   - **Định dạng đường dẫn:**
     ```text
     https://api.render.com/deploy/srv-xxxxxxxxxxxxxxxx?key=yyyyyyyy
     ```
   - **Mục đích sử dụng:** Khi gửi request HTTP POST tới URL này (ví dụ tích hợp từ GitHub Actions hoặc script CI/CD), Render sẽ tự động kích hoạt tiến trình pull code mới từ nhánh `main` và redeploy Backend mà không cần phải đăng nhập vào dashboard Render.

5. **Đường dẫn Cổng nội bộ (Internal Port & Environment Variable):**
   - Trên Render, server không cố định cổng `8000` mà tự động cấp phát một cổng ngẫu nhiên thông qua biến môi trường `$PORT` (thường là `10000`).
   - Trong lệnh khởi chạy (*Start Command*), luôn sử dụng:
     ```bash
     uvicorn app.main:app --host 0.0.0.0 --port $PORT
     ```
   - Kiểm tra trong tab **Logs**: Khi thấy dòng thông báo `Application startup complete` và `Uvicorn running on http://0.0.0.0:10000` là Backend đã kết nối mạng thành công.

---

### 7.4. Cấu hình triển khai Frontend Next.js trên Vercel (từ Monorepo)

Vercel được tối ưu hóa xuất sắc cho Next.js và hỗ trợ tính năng chọn thư mục gốc (Root Directory) cho Monorepo rất mượt mà.

#### Bước 1: Import Project vào Vercel
1. Truy cập [https://vercel.com/](https://vercel.com/) $\rightarrow$ Đăng nhập bằng tài khoản GitHub.
2. Tại trang Tổng quan (Dashboard), nhấn **Add New...** $\rightarrow$ Chọn **Project**.
3. Tại danh sách repositories, tìm repository duy nhất của dự án (`trash-classification-system`) $\rightarrow$ Nhấn **Import**.

#### Bước 2: Thiết lập Monorepo Root Directory trên Vercel
1. **Project Name:** `trash-classification-web`.
2. **Framework Preset:** Vercel tự động nhận diện là `Next.js`.
3. **Root Directory (Cốt lõi):**
   - Mặc định Vercel chọn `./`.
   - Nhấn nút **Edit** bên cạnh $\rightarrow$ Chọn thư mục: **`frontend`** $\rightarrow$ Nhấn **Continue**.
4. Các mục *Build Command* và *Output Directory* giữ nguyên mặc định.

#### Bước 3: Thiết lập Biến môi trường trên Vercel
Mở rộng mục **Environment Variables** và cấu hình:
- **Key:** `NEXT_PUBLIC_API_URL`
- **Value:** `https://trash-classification-api.onrender.com/api/v1` *(Dán URL Backend đã lấy ở Bước 7.3 kèm tiền tố `/api/v1`)*.

#### Bước 4: Deploy & Lấy URL Frontend
1. Nhấn nút **Deploy**.
2. Vercel sẽ tự động tải các packages trong `frontend/package.json` và build ứng dụng Next.js.
3. Sau 1 - 2 phút, màn hình chúc mừng xuất hiện. Bạn nhận được link chính thức:
   ```text
   https://trash-classification-web.vercel.app
   ```

---

### 7.5. Hoàn tất kết nối Fullstack khép kín (Handshake & CORS)

Để Frontend trên Vercel có thể gọi sang Backend trên Render mà không bị trình duyệt chặn bởi chính sách CORS (Cross-Origin Resource Sharing), thực hiện bước bắt tay cuối cùng:

#### Bước 1: Cập nhật CORS trên Render Backend
1. Mở lại Dashboard Render $\rightarrow$ Vào dịch vụ `trash-classification-api`.
2. Chọn tab **Environment** $\rightarrow$ Tìm biến `CORS_ORIGINS`.
3. Cập nhật thêm URL Frontend Vercel vào mảng:
   ```json
   ["http://localhost:3000", "https://trash-classification-web.vercel.app"]
   ```
4. Nhấn **Save Changes**. Render sẽ tự động cập nhật cấu hình trong vài giây.

#### Bước 2: Bảng tra cứu toàn bộ Biến môi trường kết nối

| Dịch vụ | Biến môi trường (.env) | Nguồn lấy giá trị | Mục đích sử dụng |
|:---|:---|:---|:---|
| **Vercel (FE)** | `NEXT_PUBLIC_API_URL` | Lấy từ URL Render Backend | Để Axios/Fetch ở Frontend biết địa chỉ gọi API |
| **Render (BE)** | `CORS_ORIGINS` | Lấy từ URL Vercel Frontend | Cho phép trình duyệt gọi API từ domain Vercel |
| **Render (BE)** | `SUPABASE_URL` | Lấy từ Supabase Project Settings > API | Kết nối lưu và đọc kết quả phân loại từ PostgreSQL |
| **Render (BE)** | `SUPABASE_KEY` | Lấy từ Supabase Project API keys (anon public) | Khóa xác thực an toàn gọi Supabase REST API |
| **Render (BE)** | `IMAGEKIT_PUBLIC_KEY` | Lấy từ ImageKit Developer options | Khóa API public |
| **Render (BE)** | `IMAGEKIT_PRIVATE_KEY` | Lấy từ ImageKit Developer options | Khóa bảo mật upload ảnh |
| **Render (BE)** | `IMAGEKIT_URL_ENDPOINT`| Lấy từ ImageKit Developer options | URL Endpoint CDN lưu ảnh |
| *(Dự phòng)* | `CLOUDINARY_*` / `MONGODB_URI` / `R2_*` | Cloudinary / MongoDB / R2 | Cấu hình thay thế nếu dùng |

#### Bước 3: Kịch bản Kiểm tra thông suốt toàn diện (End-to-End Verification)
1. Mở trình duyệt truy cập website Frontend: `https://trash-classification-web.vercel.app`.
2. **Kiểm tra Phân loại 1 ảnh:**
   - Kéo thả 1 bức ảnh rác thải (ví dụ: chai nhựa `plastic_bottle_01.jpg`).
   - Nhấn **Bắt đầu dự đoán**.
   - Quan sát DevTools (F12) $\rightarrow$ Tab Network: Request gửi đến `...onrender.com/api/v1/predict/single` trả về mã `200 OK`.
   - Kiểm tra giao diện: Hiển thị đúng ảnh preview, thẻ kết quả *Loại rác: Nhựa*, 3 thanh progress bar và badge *Kết quả hợp lệ*.
3. **Kiểm tra Cloudinary Storage:**
   - Chuột phải vào ảnh kết quả hoặc ảnh nhiệt XAI $\rightarrow$ Chọn *Open image in new tab*.
   - Địa chỉ ảnh có tiền tố `https://res.cloudinary.com/...` $\rightarrow$ Ảnh đã được lưu và phân phối thành công qua CDN Cloudinary.
4. **Kiểm tra Supabase Database:**
   - Vào Supabase Dashboard $\rightarrow$ Table Editor $\rightarrow$ Chọn bảng `prediction_logs`.
   - Bản ghi mới nhất xuất hiện với đầy đủ các trường: `id`, `file_name`, `image_url`, `waste_type`, `confidence`, `checkpoint_1`, `checkpoint_2`, `pipeline_type`, `status`.
5. **Kiểm tra Trang Lịch sử:**
   - Nhấn vào menu **Lịch sử** trên sidebar Frontend.
   - Bản ghi vừa dự đoán hiển thị đầu bảng. Nhấp vào dòng đó $\rightarrow$ Panel chi tiết bên phải mở ra hiển thị ảnh từ Cloudinary và thông tin chính xác.

---

### 7.6. Chiến lược UptimeRobot Kép: Chống Cold Start Render & Chống Tạm dừng Supabase (Anti-Pause 7 Days)

Để đảm bảo hệ thống phản hồi siêu tốc ngay từ lần đầu tiên truy cập và **không bao giờ bị tạm dừng hay gián đoạn dịch vụ**, dự án triển khai **chiến lược phòng thủ kép 2 tầng**:
1. **Tầng 1 (DevOps Cloud Keep-Alive):** Sử dụng **UptimeRobot** thiết lập 2 Monitor độc lập:
   - **Monitor 1 (Giữ ấm Render Backend):** Ping định kỳ mỗi 5–10 phút vào `/api/v1/health` $\rightarrow$ Triệt tiêu hiện tượng *Cold Start* (ngủ đông sau 15 phút không dùng của gói Free trên Render).
   - **Monitor 2 (Chống Pause Supabase Database):** Ping định kỳ vào REST API Supabase $\rightarrow$ Ngăn chặn Supabase tự động *Pause* (tạm dừng cơ sở dữ liệu sau 7 ngày không có truy vấn).
2. **Tầng 2 (Client Pre-warming & Đèn trạng thái UX):** Frontend tự động gửi ngầm request `GET /health` khi vừa mở trang và hiển thị đèn trạng thái trực quan ở góc Sidebar.

```
┌──────────────────────────────────────────────────────────────────────────────────────────────────┐
│                         CHIẾN LƯỢC UPTIMEROBOT KÉP GIỮ HỆ THỐNG ONLINE 24/7                      │
│                                                                                                  │
│   ┌──────────────────────────────────────────────────────────────────────────────────────────┐   │
│   │                                UPTIMEROBOT CLOUD (Gói FREE)                              │   │
│   └───────────────────────────┬──────────────────────────────────┬───────────────────────────┘   │
│                               │ (Monitor 1: mỗi 5-10 phút)       │ (Monitor 2: mỗi 12-24h)       │
│                               │ GET /api/v1/health               │ GET /rest/v1/prediction_logs  │
│                               │ (Header: none)                   │ (Header: apikey <SUPABASE_KEY>│
│                               ▼                                  ▼                               │
│                   ┌────────────────────────┐         ┌────────────────────────┐                  │
│                   │   Render Backend API   │         │   Supabase Database    │                  │
│                   │ (Luôn WARM < 300ms)    │         │ (Hoạt động 24/7,       │                  │
│                   │ (Không bao giờ ngủ)    │         │  Không bao giờ Pause)  │                  │
│                   └───────────┬────────────┘         └───────────▲────────────┘                  │
│                               │                                  │                               │
│                               └────── Gián tiếp giữ ấm ──────────┘                               │
│                                   (Mỗi lần health check, BE                                      │
│                                    gọi nhẹ Supabase SELECT 1)                                    │
│                                                                                                  │
│   [TẦNG 2: CLIENT PRE-WARMING TRÊN FRONTEND]                                                     │
│   ┌────────────────────────┐  1. Ping ngầm GET /health khi mở web                                │
│   │  Frontend Next.js App  │ ─────────────────────────────────────────┐                          │
│   │  - Hiện đèn 🟢 Sẵn sàng│ ◀────────────────────────────────────────┤                          │
│   │  - Đánh thức dự phòng  │     Status 200 OK (Model ready)          │                          │
│   └───────────┬────────────┘                                          ▼                          │
│               │ 2. Người dùng chọn ảnh                          ┌───────────┐                    │
│               └────────────────────────────────────────────────▶│ Kết quả AI│ (Trả về < 300ms)   │
│                                                                 └───────────┘                    │
└──────────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

#### Phần A: Hướng dẫn Cấu hình UptimeRobot từng bước chi tiết

##### Bước 1: Đăng ký tài khoản UptimeRobot
1. Truy cập [https://uptimerobot.com/](https://uptimerobot.com/).
2. Nhấn nút **Register for FREE** (Gói Free cho phép tạo tới 50 monitors hoàn toàn miễn phí, không yêu cầu thẻ tín dụng).
3. Xác nhận email kích hoạt và đăng nhập vào trang quản trị UptimeRobot Dashboard.

##### Bước 2: Thiết lập Monitor 1 — Giữ ấm Render Backend (Zero Cold Start)
- **Mục tiêu:** Render Free Tier tự động đưa container vào trạng thái ngủ đông (Sleep) nếu không có request trong 15 phút. Khi có người truy cập lại, server mất từ 30s đến 1 phút để khởi động lại (*Cold Start*). Monitor này ping mỗi 5–10 phút để server luôn trong trạng thái thức (*Warm*).
- **Thao tác tạo Monitor 1:**
  1. Tại Dashboard UptimeRobot, nhấn nút **+ Add New Monitor** (màu xanh lá ở góc trên).
  2. Điền chính xác các trường:
     - **Monitor Type:** Chọn `HTTP(s)`.
     - **Friendly Name:** Đặt tên gợi nhớ: `Render Backend Keep-Alive`.
     - **URL (or IP):** Nhập URL endpoint Health Check của Backend trên Render:
       ```text
       https://trash-classification-api.onrender.com/api/v1/health
       ```
     - **Monitoring Interval:** Chọn `5 minutes` hoặc `10 minutes` *(phải nhỏ hơn 15 phút)*.
     - **Monitor Timeout:** `30 seconds`.
  3. Nhấn **Create Monitor**.

##### Bước 3: Thiết lập Monitor 2 — Chống ngủ đông Supabase Database (Anti-Pause 7 Days)
- **Mục tiêu:** Supabase quy định đối với gói Free: **Nếu một dự án không có bất kỳ truy vấn nào trong 7 ngày liên tiếp, dự án sẽ tự động chuyển sang trạng thái Tạm dừng (Paused)**. Khi đó, website sẽ bị lỗi kết nối cơ sở dữ liệu và người quản trị phải vào Supabase Dashboard bấm nút *Resume* thủ công rất bất tiện.
- **Giải pháp:** Cấu hình UptimeRobot gửi một truy vấn đọc dữ liệu siêu nhẹ (chỉ lấy 1 dòng `id`) trực tiếp vào PostgREST API của Supabase kèm khóa xác thực `apikey`. Thao tác này được Supabase ghi nhận là có hoạt động thực tế, giúp cơ sở dữ liệu duy trì trạng thái **Active 24/7 vĩnh viễn**!
- **Thao tác tạo Monitor 2:**
  1. Tại Dashboard UptimeRobot, nhấn nút **+ Add New Monitor**.
  2. Điền chính xác các trường:
     - **Monitor Type:** Chọn `HTTP(s)`.
     - **Friendly Name:** Đặt tên: `Supabase Database Anti-Pause`.
     - **URL (or IP):** Ghép URL theo công thức sau:
       ```text
       https://<project-ref>.supabase.co/rest/v1/prediction_logs?select=id&limit=1
       ```
       > 💡 **Cách xác định `<project-ref>`:**  
       > Nhìn vào biến `SUPABASE_URL` của bạn (ví dụ: `https://abcdefghijklmnopq.supabase.co`), thì `<project-ref>` chính là chuỗi ký tự đứng trước `.supabase.co` (ở đây là `abcdefghijklmnopq`).  
       > URL hoàn chỉnh sẽ là: `https://abcdefghijklmnopq.supabase.co/rest/v1/prediction_logs?select=id&limit=1`
     - **Monitoring Interval:** Chọn `12 hours` hoặc `1 day` (hoặc `10 minutes` đều được, không ảnh hưởng đến quota Supabase vì truy vấn chỉ đọc 1 id duy nhất).
     - **Monitor Timeout:** `30 seconds`.
  3. **Cấu hình Header xác thực bắt buộc (Bảo mật API Key):**
     - Cuộn xuống dưới cùng của hộp thoại tạo Monitor, click vào **Advanced Settings** để mở rộng.
     - Tìm mục **Custom HTTP Headers** (hoặc *HTTP Headers*):
       * Ô **Header Name:** Nhập chính xác chữ thường: `apikey`
       * Ô **Header Value:** Dán chuỗi `SUPABASE_KEY` (khóa `anon public` JWT dài bạn đã lấy ở Bước 7.1).
  4. Nhấn **Create Monitor**.

##### Bước 4: Cơ chế Bảo vệ Kép (Double Keep-Alive Assurance)
Bên cạnh Monitor 2 gọi trực tiếp vào Supabase, hệ thống còn được trang bị **cơ chế giữ ấm ngầm từ Backend**:
- Mỗi khi Monitor 1 ping vào `/api/v1/health` của Render (mỗi 5–10 phút), hàm kiểm tra sức khỏe của Backend FastAPI (`_watch_dependencies`) sẽ tự động gọi hàm `SupabaseHistory.check()`:
  ```python
  # Trích từ backend/app/db/supabase_db.py
  async def check(self) -> None:
      res = self.client.table("prediction_logs").select("id").limit(1).execute()
  ```
- Nhờ vậy, ngay cả khi người dùng quên cấu hình Monitor 2 trên UptimeRobot thì chỉ cần Monitor 1 hoạt động, **Supabase vẫn tự động được giữ ấm liên tục và không bao giờ bị tạm dừng!**

##### Bước 5: Xác nhận trạng thái hoạt động trên UptimeRobot
1. Quay lại trang Dashboard UptimeRobot sau khoảng 1–2 phút.
2. Kiểm tra danh sách màn hình:
   - `Render Backend Keep-Alive`: Hiển thị thanh màu xanh lá **`Up (100%)`**.
   - `Supabase Database Anti-Pause`: Hiển thị thanh màu xanh lá **`Up (100%)`**.
3. Cả 2 hạ tầng Backend và Database đã được bảo vệ hoàn toàn tự động!

---

#### Phần B: Triển khai Pre-warming Ping & Đèn trạng thái trên Frontend (Tầng Client UX)

- **Mục đích:**
  1. Đóng vai trò phao cứu sinh dự phòng (khi server vừa restart sau khi deploy bản cập nhật mới hoặc trước chu kỳ ping của UptimeRobot).
  2. Hiển thị một chấm đèn trực quan ở chân Sidebar giúp người dùng biết máy chủ AI đã sẵn sàng trước khi tải ảnh lên.

- **Mã nguồn Hook kiểm tra trạng thái (`frontend/src/hooks/useHealthCheck.ts`):**
  ```typescript
  import { useState, useEffect } from 'react';
  import axios from 'axios';

  export type ServerStatus = 'connecting' | 'healthy' | 'error';

  export function useHealthCheck() {
    const [status, setStatus] = useState<ServerStatus>('connecting');

    useEffect(() => {
      let isMounted = true;
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

      const checkHealth = async () => {
        try {
          const res = await axios.get(`${apiUrl}/health`, { timeout: 8000 });
          if (isMounted && res.status === 200 && res.data?.status === 'healthy') {
            setStatus('healthy');
          } else if (isMounted) {
            setStatus('error');
          }
        } catch {
          if (isMounted) setStatus('error');
        }
      };

      checkHealth();
      // Ping lại nhẹ sau mỗi 2 phút khi người dùng còn mở tab
      const interval = setInterval(checkHealth, 120000);
      return () => {
        isMounted = false;
        clearInterval(interval);
      };
    }, []);

    return status;
  }
  ```

- **Mã nguồn Component Đèn trạng thái (`frontend/src/components/layout/SystemStatusBadge.tsx`):**
  ```tsx
  import React from 'react';
  import { useHealthCheck } from '@/hooks/useHealthCheck';

  export const SystemStatusBadge: React.FC = () => {
    const status = useHealthCheck();

    return (
      <div className="flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-medium bg-slate-800/80 border border-slate-700/50">
        {status === 'healthy' && (
          <>
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
            </span>
            <span className="text-emerald-400">Máy chủ AI: Sẵn sàng</span>
          </>
        )}
        {status === 'connecting' && (
          <>
            <span className="h-2 w-2 rounded-full bg-amber-400 animate-pulse"></span>
            <span className="text-amber-300">Đang đánh thức máy chủ...</span>
          </>
        )}
        {status === 'error' && (
          <>
            <span className="h-2 w-2 rounded-full bg-rose-500"></span>
            <span className="text-rose-400">Mất kết nối máy chủ</span>
          </>
        )}
      </div>
    );
  };
  ```

👉 **Hiệu quả tổng hợp của Chiến lược kép:** Hệ thống vừa có lớp bảo vệ DevOps tự động 24/7 từ bên ngoài, vừa có giao diện chuyên nghiệp, minh bạch và thân thiện với người dùng ngay khi vừa mở trang web.

---

> 📌 **Ghi chú quan trọng cho Đội ngũ phát triển:**  
> - Luôn đối chiếu giao diện thực tế với 4 hình ảnh tham chiếu trong thư mục [Giao diện](./Giao%20diện) trong quá trình cắt HTML/CSS để đảm bảo độ chính xác cao nhất về màu sắc và layout.  
> - Khóa bảo mật các API keys (`SUPABASE_KEY`, `CLOUDINARY_API_SECRET`, `MONGODB_URI`, `R2_SECRET_KEY`) trong file `.env`, tuyệt đối không commit lên GitHub repository.
