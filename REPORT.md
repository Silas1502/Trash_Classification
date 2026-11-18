# Báo cáo thực hiện website phân loại rác

Đối chiếu với [kế hoạch website](docs/PLAN_WEBSITE.md). Báo cáo ghi nhận kết quả đến ngày 18/11/2026 và phân biệt giữa kiểm tra trên dịch vụ đang chạy, kiểm thử local và đối chiếu mã nguồn.

## 1. Kết quả theo từng công việc

### Backend và mô hình

| Mục | Công việc | Kết quả |
| --- | --- | --- |
| B1 | FastAPI và tài liệu API | FastAPI phục vụ API dưới tiền tố `/api/v1`, có [Swagger UI](https://trash-onnx-free-probe.onrender.com/docs) và [ReDoc](https://trash-onnx-free-probe.onrender.com/redoc). |
| B2 | Kiểm tra trạng thái | Đã kiểm thử GET và HEAD. GET trên Render trả `healthy`, mô hình đã nạp, Supabase kết nối và ImageKit truy cập được. |
| B3 | Dự đoán một ảnh | API nhận ảnh multipart, giải mã RGB, cắt vuông, resize AREA về 320×320 và chạy 5-view TTA. Kiểm thử local qua với mô hình ONNX thật và dịch vụ lưu trữ giả lập. Phản hồi trả loại rác, hai chốt, URL ảnh và thời gian xử lý. |
| B4 | Dự đoán nhiều ảnh và thư mục | Frontend gửi tuần tự từng lô tối đa 4 ảnh và 32 MiB. Render xử lý từng ảnh và giải phóng bộ đệm của ảnh sau khi xử lý. API trả tiến độ, kết quả và lỗi theo từng ảnh. Đã thử lô 3 ảnh trên Render và kiểm thử local lô gồm 2 ảnh hợp lệ, 1 ảnh lỗi. |
| B5 | Hai chốt an toàn | Độ tin cậy so với ngưỡng theo lớp, biên khoảng cách so với ngưỡng chung. Cả hai đạt thì chuyển luồng Tự động, nếu một chốt trượt thì chuyển Thủ công và trả lý do. Bộ kiểm thử đối chiếu ONNX với TensorFlow trên 64 ảnh ghi nhận cùng nhãn và quyết định an toàn. |
| B6 | Xác thực dữ liệu đầu vào | Giới hạn mặc định 8 MiB và 16 MP mỗi ảnh. Đã kiểm thử từ chối MIME sai, báo lỗi ảnh hỏng trong lô và xử lý JPEG RGB cùng PNG RGBA hợp lệ ở 4000×4000. |
| B7 | Danh sách lịch sử | GET trên Render trả dữ liệu Supabase có phân trang. Mã nguồn hỗ trợ sắp xếp theo thời gian, tìm tên ảnh và lọc theo loại rác, luồng, thời gian. |
| B8 | Chi tiết một bản ghi | GET theo ID trên Render trả kết quả và có đủ ba URL ảnh gốc, Grad-CAM và Spatial Energy. |
| B9 | Xuất CSV | Endpoint xuất dữ liệu theo bộ lọc và đặt trần truy vấn 5.000 bản ghi. Giao diện có nút tải CSV. |
| B10 | CORS và xử lý lỗi | Request kiểm tra trạng thái từ origin Vercel nhận đúng header CORS. Backend chuẩn hóa lỗi thành JSON. Lô ảnh có thể trả thành công một phần. |
| B11 | Thông tin mô hình | Đã kiểm thử `/model-info` trả mô hình thật và 5-view TTA. Endpoint công bố checkpoint, kích thước đầu vào và cấu hình ngưỡng đang nạp. |
| B12 | Grad-CAM và Spatial Energy | Backend tạo hai ảnh phủ nhiệt JET trên vùng ảnh đầu vào đã cắt. ONNX dùng đồ thị gradient cho Grad-CAM và đặc trưng không gian cho Spatial Energy. Kiểm thử local xác nhận tạo ảnh và kết quả thật trên Render có đủ URL. |

### Cơ sở dữ liệu và lưu trữ

| Mục | Công việc | Kết quả |
| --- | --- | --- |
| D1 | Cấu hình ImageKit | Render báo kho ảnh truy cập được. API lịch sử trả URL ba ảnh từ kết quả thực tế. |
| D2 | Adapter lưu ảnh | Backend lưu ảnh gốc và hai ảnh XAI qua ImageKit. Có adapter Supabase Storage làm phương án dự phòng. Bản Render đang dùng ImageKit. |
| D3 | Kết nối Supabase | Backend đọc và ghi lịch sử vào bảng `prediction_logs`. Đã đọc danh sách và chi tiết trên dịch vụ Render. |
| D4 | Cấu trúc bản ghi | Bản ghi lưu kết quả, ngưỡng, trạng thái, URL ảnh và metadata. Thời gian xử lý mới nằm trong `metadata.processing_time_ms` và dùng cột JSON hiện có. Bản ghi cũ vẫn đọc được. |
| D5 | Thống kê theo lô | API trả số ảnh đã xử lý, đang chờ, thành công và lỗi, cùng tỷ lệ hoàn thành. Kết quả hợp lệ được lưu theo từng ảnh. |
| D6 | Chỉ mục và tìm kiếm | SQL trong kế hoạch định nghĩa chỉ mục theo `created_at`, `waste_type` và `pipeline_type`. Adapter tìm tên ảnh bằng `ILIKE`. Sự tồn tại của các chỉ mục trên Supabase chưa được kiểm tra trực tiếp trong lượt rà soát này. |
| D7 | Lỗi dịch vụ phụ thuộc | Backend dò Supabase và kho ảnh theo chu kỳ mặc định 30 giây. Kiểm thử local xác nhận API trả 503 khi thiếu cấu hình cloud và báo lỗi riêng từng ảnh trong lô. |

### Frontend

| Mục | Công việc | Kết quả |
| --- | --- | --- |
| F1 | Sidebar điều hướng | Có hai mục Phân loại và Lịch sử, mục đang mở được đánh dấu và sidebar hiển thị trạng thái hệ thống. |
| F2 | Màn hình một ảnh | Có chọn hoặc kéo thả ảnh, xem trước, dự đoán, làm mới, kết quả hai chốt, gợi ý, thời gian xử lý và trình xem ảnh XAI. |
| F3 | Màn hình nhiều ảnh | Có chọn nhiều ảnh hoặc thư mục, bốn chỉ số tiến độ, dừng sau lô đang chạy, bảng kết quả có thời gian xử lý, lọc loại rác và tìm tên tệp. |
| F4 | Danh sách lịch sử | Có tìm kiếm, lọc, phân trang và xuất CSV. Đã gỡ chức năng xóa lịch sử khỏi giao diện và API theo yêu cầu. |
| F5 | Chi tiết dự đoán | Cửa sổ chi tiết hiển thị ảnh gốc, Grad-CAM, Spatial Energy, hai chốt, luồng, thời điểm dự đoán và thời gian xử lý nếu bản ghi có metadata. |
| F6 | Trạng thái tải | Có trạng thái chờ khi dự đoán một ảnh hoặc tải lịch sử và thanh tiến độ cập nhật sau từng lô. |
| F7 | Thông báo | Giao diện báo lỗi tải ảnh, lỗi API và thông báo khi tải CSV. |
| F8 | Responsive | CSS có các breakpoint cho bố cục, bộ lọc và bảng. Lượt rà soát này chưa đối chiếu lại bốn ảnh tham chiếu trên mọi kích thước. |
| F9 | Trình xem XAI | Giao diện cho phép chuyển giữa ảnh gốc và hai ảnh giải thích trong kết quả dự đoán và chi tiết lịch sử. |
| F10 | Đèn trạng thái | Sidebar dùng nhãn **Hệ thống**. Trình duyệt gọi health với timeout 5 giây và lên lịch kiểm tra lại sau 30 giây. |

### Triển khai và giám sát

| Mục | Công việc | Kết quả |
| --- | --- | --- |
| P1 | Backend Render | Render API xác nhận nhánh `main`, root `backend`, Native Python, gói Free tại Singapore và Auto-Deploy On Commit. Build dùng file lock của ONNX, lệnh chạy là `bash start-render.sh`. |
| P2 | Frontend Vercel | [Website Vercel](https://trash-classification-seven.vercel.app) trả HTTP 200 ở trang Phân loại. Theo cấu hình đã lập trong kế hoạch, Vercel dùng root `frontend` của cùng monorepo. |
| P3 | ImageKit | Backend production báo kho ảnh truy cập được và trả URL ảnh gốc cùng hai ảnh XAI trong chi tiết dự đoán. |
| P4 | Supabase | Backend production báo kết nối thành công và trả dữ liệu lịch sử. |
| P5 | Biến môi trường | Render giải mã mô hình từ Secret File và khởi động ONNX. Frontend dùng `NEXT_PUBLIC_API_URL` để gọi API. Báo cáo chỉ ghi tên biến cấu hình. |
| P6 | Kết nối CORS | Render trả `Access-Control-Allow-Origin` đúng tên miền Vercel trên yêu cầu kiểm tra thực tế. |
| P7 | UptimeRobot | Monitor HTTP của Render đã kích hoạt. Kế hoạch ghi nhận chu kỳ khoảng 5 phút từ log ngày 18/11/2026. Chưa cấu hình monitor riêng cho Supabase. Backend có truy vấn kiểm tra kết nối Supabase định kỳ. |

## 2. Bàn giao và nghiệm thu

- Giai đoạn 1 bàn giao mô hình ConvNeXt-Tiny, hai chốt, bảng lịch sử và adapter lưu trữ. Giai đoạn 2 bàn giao API dự đoán, lịch sử và Swagger. Giai đoạn 3 bàn giao các màn hình Next.js. Giai đoạn 4 bàn giao URL Vercel, Render và báo cáo này.
- Các luồng demo gồm dự đoán một ảnh, dự đoán theo thư mục và tra cứu lịch sử. Điểm số theo thang 100 trong kế hoạch cần được chấm khi nghiệm thu, bao gồm đối chiếu giao diện với ảnh tham chiếu và diễn tập toàn bộ các luồng.
- **Thời gian xử lý** gồm tiền xử lý ảnh, suy luận và tạo XAI. Phép đo loại trừ thời gian truyền mạng, tải ảnh lên ImageKit và ghi lịch sử Supabase.
- Script kiểm thử API local chạy với ONNX thật, kho ảnh và lịch sử giả lập. Peak working set của **tiến trình Python trên Windows** là khoảng **419,48 MiB**. Số liệu container Render được ghi riêng bên dưới.
- Build production Next.js và kiểm tra TypeScript đã qua. Kiểm thử local xác nhận API chặn phương thức DELETE lịch sử và thời gian xử lý có mặt trong phản hồi ảnh đơn, lô ảnh và metadata lịch sử.
- Dọn các cache Python, ảnh chụp kiểm thử có thể tạo lại và gói nén triển khai Uppcoder cũ. Giữ các thư mục dữ liệu `data/datasets`, `data/splits`, `data/zips`, checkpoint và kết quả thí nghiệm.

## 3. Cách xem dung lượng Render

1. Mở [dịch vụ Render](https://dashboard.render.com/web/srv-dbu73mlckfvc73ba62a0), vào **Metrics → Application Metrics → Memory Usage** và chọn hiển thị giá trị thực. Chọn khoảng thời gian ngắn, thử một ảnh hoặc một lô rồi rê chuột trên biểu đồ để đọc RAM của instance. [Tài liệu Render Metrics](https://render.com/docs/service-metrics#cpu-and-memory-usage)
2. Lần đo qua Render API ngày 18/11/2026 lúc 09:56 giờ Việt Nam ghi nhận **347,49 MiB RAM** trên giới hạn **512 MiB**. Điểm cao nhất của chuỗi mẫu một giờ là **357,02 MiB**, lấy mẫu 60 giây. Mẫu theo phút có thể bỏ qua đỉnh ngắn trong lúc xử lý. Đây là RAM instance Render.
3. **Disk** của Web Service Free là filesystem tạm. API Disk Usage trả về chuỗi rỗng và Dashboard chỉ có biểu đồ Disk Usage cho dịch vụ có lưu trữ bền vững. Trong **Logs**, tìm `RENDER_ONNX` và đọc `filesystem_free_bytes` ở dòng `stage: loaded` sau lần khởi động. Trường này là số byte còn trống trên filesystem chứa thư mục tạm, không phải dung lượng riêng của mã nguồn, mô hình hoặc toàn bộ dịch vụ. [Giới hạn Render Free](https://render.com/docs/free#local-files-lost-on-redeploy)
