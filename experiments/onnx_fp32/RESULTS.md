# Kết quả thử nghiệm ONNX FP32 — 17/11/2026

## Kết luận

Bản ONNX chạy đủ dự đoán 5-view TTA, Grad-CAM và Spatial Energy mà không cài/nạp
TensorFlow, Keras hoặc PyTorch trong môi trường serving. Trên tập con 64 ảnh đã
kiểm tra, không đổi nhãn, đồng thuận TTA hoặc quyết định an toàn. Mức dùng RAM và
thời gian xử lý giảm rõ trên Windows. Chưa triển khai lên nền tảng nào và chưa
xác nhận container Linux bị giới hạn 512 MB.

## Giữ nguyên mô hình

- Checkpoint gốc: `checkpoints/convnext_tiny/best_v2_convnext_retrained_inference.keras`.
- SHA256: `866206ad9084f8feba2d67ccb550ac76965a8ce7316256ec0560a676f7b1e7a8`.
- Checkpoint vẫn có kích thước 119.190.756 byte; không sửa hoặc huấn luyện lại.
- FP32, input 320×320, 5-view TTA, lớp spatial và ngưỡng an toàn giữ nguyên.
- Hai đồ thị ONNX tổng 130.437.217 byte, khoảng 124,39 MiB. Artifact lớn hơn
  checkpoint khoảng 10,73 MiB vì đóng gói thêm đồ thị gradient. Phần tiết kiệm
  disk chủ yếu đến từ bỏ runtime TensorFlow đầy đủ, không phải nén trọng số.

## So kết quả trên 64 ảnh

Chọn đều 16 ảnh mỗi lớp glass, metal, paper, plastic trong tập
`data/datasets/MyTrashNet_Test_10Percent`. Danh sách trong `results/cases.json`.
Tham chiếu và ONNX chạy ở hai tiến trình khác nhau, không gọi dịch vụ cloud.

| Tiêu chí | TensorFlow | ONNX |
|---|---:|---:|
| Accuracy trên tập con | 96,875% | 96,875% |
| Macro F1 trên tập con | 0,9687347 | 0,9687347 |
| Số ảnh khác nhãn so với TensorFlow | — | 0/64 |
| Số ảnh khác đồng thuận TTA | — | 0/64 |
| Khác quyết định an toàn, cả hai chế độ adaptive | — | 0 |

Sai số tuyệt đối lớn nhất:

| Giá trị | Sai số | Ngưỡng chấp nhận đặt trước |
|---|---:|---:|
| Xác suất, thang 0–1 | 9,536743e-7 | 1e-4 |
| Grad-CAM đã chuẩn hóa, thang 0–1 | 1,856089e-4 | 5e-3 |
| Spatial Energy đã chuẩn hóa, thang 0–1 | 1,072884e-5 | 1e-3 |

Đã kiểm tra thêm 14 trường hợp giải mã ảnh/màu/EXIF và 7 kích thước resize AREA
(bao gồm 1×1, 17×29, 288×288, kích thước lẻ và resize xuống). EXIF và chuyển RGB
khớp từng pixel; sai số resize tối đa trong các trường hợp này là 6,103516e-5
trên thang giá trị ảnh 0–255.

Đây là tương đương số học trong phạm vi đã thử, không phải giống từng bit hoặc
bảo đảm chất lượng trên mọi ảnh tương lai. Chi tiết cả tensor/gradient và từng
ảnh nằm trong `results/comparison.json`; không chỉ so sánh nhãn đầu ra.

## Tài nguyên: tiến trình Python trên Windows

Đo lần lượt hai tiến trình, mỗi bên cùng 4 ảnh (mỗi lớp một ảnh), 2 thread, đủ
5-view TTA, hai XAI và mã hóa JPEG; không bao gồm upload hoặc ghi lịch sử cloud.
Thời gian request không bao gồm khởi động; peak RAM có bao gồm khởi động.

| Chỉ số | TensorFlow 2.20.0 | ONNX Runtime 1.29.0 |
|---|---:|---:|
| RSS sau nạp mô hình | 819,53 MiB | 195,57 MiB |
| Peak working set toàn lượt đo | 1.031,53 MiB | 260,66 MiB |
| Trung bình/ảnh | 5,356 giây | 1,147 giây |
| Trung vị/ảnh | 5,298 giây | 1,133 giây |
| CPU cho 4 request | 35,531 giây | 9,391 giây |
| Nạp mô hình và import trong worker | 41,711 giây | 0,700 giây |
| Disk của thư mục package chính trên Windows | 1.302,42 MiB | 43,13 MiB |

Trong lượt đo này peak RAM giảm khoảng 74,7%, thời gian trung bình giảm khoảng
4,67 lần. Thời gian phụ thuộc máy và tải nền; 4 request không đại diện mọi ảnh.
Không so trực tiếp các số RAM này với tổng container/RAM Python trên Uppcoder.
Disk ở bảng là thư mục package chính, không phải tổng môi trường hoặc Docker
image. Venv ONNX gồm các phụ thuộc API và gói đo/test khoảng 277,6 MB trên disk;
hai mô hình ONNX khoảng 130,4 MB, tính riêng. Không có TensorFlow trong venv này.

## API và ảnh lớn

Kiểm tra health GET/HEAD, model-info, dự đoán đơn, lô gồm hai ảnh hợp lệ và một
ảnh lỗi, từ chối MIME không hỗ trợ, trả 503 khi thiếu cấu hình cloud, cùng ảnh
JPEG RGB và PNG RGBA 4000×4000 (16 megapixel, đúng giới hạn hiện tại).

- Qua tất cả kiểm tra, không nạp TensorFlow/Keras/PyTorch.
- Peak working set tiến trình API trong lượt cuối: **440.020.992 byte = 419,64 MiB**.
- RSS cuối: 323.842.048 byte, khoảng 308,84 MiB.
- Lưu trữ và lịch sử dùng đối tượng giả trong RAM; không gửi ảnh/ghi dữ liệu lên
  Supabase hoặc ImageKit.
- API TensorFlow mặc định cũng qua kiểm tra hồi quy health/model-info/predict
  với predictor mô phỏng; 64 ảnh tham chiếu dùng mô hình TensorFlow thật.

Như vậy có cơ sở thử máy chủ 512 MB, nhưng còn phải đo tổng container Linux,
startup, request đồng thời và SDK thật trước khi khẳng định phù hợp. Máy hiện
không có Docker hoặc distro WSL sẵn để chạy phép thử container này.

## Cách xem và chạy

[Hướng dẫn PowerShell, export, kiểm thử và Docker](README.md).
Entry point thử: `experiments.onnx_fp32.app:app`, cổng local đề xuất 8001.
Entry point TensorFlow hiện tại, cấu hình frontend và dịch vụ Uppcoder/Vercel
chưa chuyển sang ONNX. Không commit, push hoặc deploy trong lượt thử này.
