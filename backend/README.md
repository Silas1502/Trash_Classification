# Backend phân loại rác

Từ thư mục `backend/`, dùng Python 3.12 và chạy:

```powershell
python -m pip install -r requirements.txt
Copy-Item .env.example .env
uvicorn app.main:app --reload
```

Swagger ở `http://127.0.0.1:8000/docs`. Điền thông tin Supabase, ImageKit và origin của frontend trong `.env` để lưu dự đoán thật và truy vấn lịch sử. Nếu bỏ cấu hình ImageKit, backend dùng bucket `trash-images` trên Supabase Storage. Tên file gửi qua multipart là `file` cho dự đoán đơn và `files` (lặp lại cho từng ảnh) cho dự đoán theo lô.

Backend ưu tiên `backend/checkpoints/best_v2_convnext_retrained.keras` và cũng nhận checkpoint hiện có trong `checkpoints/convnext_tiny/` ở gốc monorepo. Có thể đặt `MODEL_PATH` thành đường dẫn tuyệt đối hoặc đường dẫn tính từ `backend/`. Khi thiếu file, dự đoán thử trả `is_mock: true` và URL ảnh rỗng (`null`). Kết quả mô phỏng chỉ xuất hiện trong phản hồi HTTP.

Mặc định `ADAPTIVE_ASSESSMENT_ENABLED=false`. `Tự động` yêu cầu cả hai chốt cơ sở đạt ngưỡng. Dự đoán trượt một trong hai chốt chuyển sang `Thủ công`. Khi `TTA_VIEWS=5`, TTA vẫn tính xác suất trung bình của các biến thể ảnh.

`ADAPTIVE_ASSESSMENT_ENABLED=true` phục hồi hai nhánh xét lại bằng điểm bù trừ và đồng thuận TTA của cơ chế cũ sau khi khởi động lại. Cấu hình ngưỡng nằm trong `app/core/safety_thresholds.json` hoặc file được chỉ định bởi `SAFETY_THRESHOLDS_PATH`. `model-info` cho biết cấu hình đang dùng. Grad-CAM và bản đồ năng lượng phủ trên ảnh crop 320×320 trước khi chuẩn hóa.

## Render Native Python

Đặt **Branch** là `main`, **Root Directory** là `backend` và **Runtime** là Python. Phiên bản Python được chọn trong `.python-version`.

| Cài đặt | Giá trị |
| --- | --- |
| Build Command | `python -m pip install -r onnx_fp32/requirements-runtime.lock.txt` |
| Start Command | `bash start-render.sh` |
| Health Check Path | `/api/v1/health` |

`start-render.sh` giải mã và xác minh mô hình ONNX từ `model-parts/` trước khi khởi động FastAPI. Cấu hình tệp bí mật `onnx-model-key` và các biến Supabase, ImageKit, `CORS_ORIGINS` trong **Environment** của dịch vụ Render.
