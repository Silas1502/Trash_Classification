# Thử nghiệm ConvNeXt-Tiny ONNX FP32

Bản chạy riêng của backend, dùng nguyên trọng số checkpoint inference, đầu vào
320×320, 5-view TTA, Grad-CAM và Spatial Energy. Không lượng tử hóa, không huấn
luyện lại, không thay ngưỡng an toàn. Entry point production `app.main:app` vẫn
dùng TensorFlow; bản này dùng `experiments.onnx_fp32.app:app`.

## Những gì được chuyển

- `forward.onnx`: logits, tensor spatial và nhánh residual skip trong một đồ thị
  chia sẻ trọng số. Không nạp ba bản backbone.
- `gradient.onnx`: logits và đạo hàm của logit lớp được chọn đối với tensor
  spatial. Đây là đồ thị đạo hàm xuất từ GradientTape, không thay Grad-CAM bằng
  phương pháp giải thích khác. Skip connection và các điểm cực đại bằng nhau
  được xử lý bởi chính biểu thức gradient gốc.
- Resize AREA dùng tọa độ float32 bất đối xứng tương ứng TensorFlow. Không dùng
  OpenCV INTER_AREA để thay resize phóng lớn của view TTA thứ năm vì quy tắc
  upsampling của chúng khác nhau.
- Giải mã ảnh theo từng dải, áp dụng EXIF tại chỗ, không tạo bản sao float32 toàn
  ảnh gốc. Các thay đổi này giảm đỉnh RAM ở ảnh lớn, không giảm kích thước đầu
  vào mô hình hoặc giới hạn ảnh được chấp nhận.
- Chạy từng ảnh và từng view. API đơn/lô, lưu lịch sử và lưu ảnh dùng chung các
  route hiện có. `SMART_CROP=true` bị từ chối vì chưa nằm trong phạm vi kiểm chứng.

Bộ chuyển đổi cần hạ ba phép toán sang biểu thức ONNX tương đương: các Conv2D
chia nhóm theo từng kênh thành depthwise convolution cùng kernel; `Erfc(x)` thành
`1-Erf(x)`; `RsqrtGrad(y,dy)` thành `-0.5*dy*y³`. Do thứ tự tính và phép toán số
thực khác nhau, không cam kết giống từng bit. Manifest ghi rõ các phép hạ này,
SHA256 checkpoint, cấu hình ngưỡng và từng artifact.

## Chạy bản đã tạo trên máy này

Mở PowerShell tại thư mục gốc dự án:

```powershell
Set-Location -LiteralPath 'C:\Users\HP\Downloads\KLTN (code)'
$env:PYTHONPATH = "$PWD\backend;$PWD"
& '.\.venv\onnx-runtime\Scripts\python.exe' -m uvicorn experiments.onnx_fp32.app:app --host 127.0.0.1 --port 8001
```

Swagger: http://127.0.0.1:8001/docs ; health: http://127.0.0.1:8001/api/v1/health.
Cấu hình Supabase/ImageKit dùng `backend/.env` hoặc biến môi trường như backend
hiện tại. Không sao chép khóa vào mã hay Docker image. Chưa đổi API URL frontend
hoặc triển khai bản này lên Uppcoder/Vercel. Thiếu cấu hình cloud thì API dự đoán
trả 503 như backend hiện tại, không âm thầm tạo dữ liệu mô phỏng.

`ONNX_MODEL_DIR` chọn thư mục artifacts; `ONNX_THREADS` mặc định 2. Chỉ chạy một
uvicorn worker để tránh nạp thêm bản mô hình.

## Tái tạo độc lập

Môi trường chuyển đổi dùng TensorFlow 2.20.0, Keras 3.13.2, tf2onnx 1.17.0,
ONNX 1.17.0 và protobuf 5.x. Không cài các gói chuyển đổi vào môi trường serving.

```powershell
python -m venv --system-site-packages '.venv\onnx-export'
& '.\.venv\onnx-export\Scripts\python.exe' -m pip install -r experiments/onnx_fp32/requirements-export.txt
& '.\.venv\onnx-export\Scripts\python.exe' -m experiments.onnx_fp32.export

python -m venv '.venv\onnx-runtime'
& '.\.venv\onnx-runtime\Scripts\python.exe' -m pip install -r experiments/onnx_fp32/requirements-runtime.lock.txt psutil
& '.\.venv\onnx-export\Scripts\python.exe' -m experiments.onnx_fp32.verify --per-class 16 --onnx-python '.venv\onnx-runtime\Scripts\python.exe'
& '.\.venv\onnx-runtime\Scripts\python.exe' -m experiments.onnx_fp32.check_api
& '.\.venv\onnx-export\Scripts\python.exe' -m experiments.onnx_fp32.check_preprocessing --tensorflow
& '.\.venv\onnx-export\Scripts\python.exe' -m experiments.onnx_fp32.check_tensorflow_api
```

`--system-site-packages` ở bước export chỉ phù hợp nếu Python gốc đã có bộ
TensorFlow/Keras tương thích trên. Trên máy khác, dùng venv thông thường và cài
TensorFlow/Keras tương ứng vào venv export. Không sửa môi trường Python chung.

Kiểm chứng lấy 16 ảnh mỗi lớp từ `data/datasets/MyTrashNet_Test_10Percent`, tổng
64 ảnh có đường dẫn được ghi trong `results/cases.json`. Hai runtime chạy trong
hai tiến trình riêng; ONNX chạy trong venv không có TensorFlow. So sánh tiền xử lý,
xác suất, nhãn, đồng thuận TTA, cả hai chế độ safety gate, gradient và heatmap.
Renderer JPEG tham chiếu gọi mã TensorFlow production. Sai số chấp nhận tối đa:
xác suất 1e-4, Grad-CAM chuẩn hóa 5e-3, Spatial Energy chuẩn hóa 1e-3; yêu cầu không
có sai nhãn, đồng thuận TTA hoặc quyết định an toàn. Không coi kết quả trên tập
con là bảo đảm chính xác trên mọi ảnh tương lai.

## Đo RAM, CPU, disk và thời gian

Sau khi đã chạy verify, chạy lần lượt, không chạy đồng thời:

```powershell
& '.\.venv\onnx-export\Scripts\python.exe' -m experiments.onnx_fp32.benchmark --engine tensorflow --repeat 1 --images-per-class 1
& '.\.venv\onnx-runtime\Scripts\python.exe' -m experiments.onnx_fp32.benchmark --engine onnx --repeat 1 --images-per-class 1
```

Lệnh trên dùng 4 ảnh, mỗi lớp một ảnh, 5-view TTA, hai XAI và mã hóa JPEG. Mặc định
`--images-per-class 2` và `--repeat 3` dùng 24 request. Báo cáo lưu ở
`results/benchmark-*.json`. RAM là working set/RSS và peak working set của **tiến
trình Python trên Windows**, không phải tổng container Linux. Disk thư viện là
tổng tệp của thư mục package được cài; disk artifact được tính riêng. Thời gian
request không bao gồm khởi động/nạp mô hình, nhưng peak RAM có bao gồm giai đoạn đó.
Không suy trực tiếp từ số này rằng container 512 MB chắc chắn chạy được. Cần đo
container Linux với giới hạn RAM thực tế trước khi chuyển nền tảng.

`results/` và `artifacts/` được bỏ qua bởi Git. Chúng chứa dữ liệu thử và artifact
lớn; không tự động đẩy lên GitHub.

## Render Free với Python

Render chạy từ `main/backend` theo [cấu hình backend](../../backend/README.md#render-native-python).
Để đóng gói mô hình ONNX mới, chạy từ thư mục gốc dự án:

```powershell
& '.\.venv\onnx-runtime\Scripts\python.exe' -m experiments.onnx_fp32.prepare_render
```

Script dùng khóa hiện có trong `.venv/render-onnx-model-key.txt` và xác minh SHA256
sau khi giải mã thử. Gói hoàn chỉnh nằm trong `.venv/render-model-parts/` để bạn
kiểm tra trước khi thay bộ tệp trong `backend/model-parts/`. Secret File
`onnx-model-key` trên Render chứa cùng khóa, được lưu riêng khỏi Git.

Đặt `ONNX_STARTUP_PROBE=1` cho lần thử để chạy hai ảnh tổng hợp, gồm JPEG
720×720 và PNG RGBA 4000×4000. Bộ dò in các bản ghi `RENDER_ONNX` trong Logs,
gồm thời gian chạy, CPU process, bộ đếm RAM cgroup nếu hệ thống cung cấp, và
dung lượng filesystem trước/sau. Đối chiếu số đo này với biểu đồ RAM của Render.
Ảnh tổng hợp chạy qua tiền xử lý, dự đoán và tạo hai JPEG XAI trong RAM.
Để thử các route dự đoán HTTP cùng ghi lịch sử, cần cấu hình Supabase và
ImageKit riêng cho dịch vụ Render theo biến môi trường backend.
