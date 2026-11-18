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
| B13 | Thống kê lịch sử | Đã thêm `GET /api/v1/history/statistics` với tổng số bản ghi và số lượng theo loại rác, luồng xử lý. Kiểm thử bằng PostgREST giả lập xác nhận tính cả hai ngày theo UTC+7, chặn khoảng ngày đảo và trả 0 cho khoảng trống. |
| B14 | Dữ liệu biểu đồ lịch sử | Đã thêm `GET /api/v1/history/trends`, hỗ trợ Hôm nay cùng các khoảng 7, 30, 90 ngày tính theo giờ Việt Nam. API Hôm nay trả 24 mốc giờ, giới hạn dữ liệu đến hiện tại và đánh dấu giờ tương lai. Kiểm thử xác nhận biên 00:00, thời điểm hiện tại, chuyển ngày và đếm đủ hơn 500 bản ghi ở các trang khác nhau. |
| B15 | Số liệu theo ngày | Đã thêm `GET /api/v1/history/daily` với khoảng ngày và số trang. Kiểm thử API xác nhận 5 ngày mỗi trang, trang cuối có thể ít hơn, tính cả hai đầu theo UTC+7, ngày trống trả 0 và trang vượt phạm vi trả danh sách trống. |

### Cơ sở dữ liệu và lưu trữ

| Mục | Công việc | Kết quả |
| --- | --- | --- |
| D1 | Cấu hình ImageKit | Render báo kho ảnh truy cập được. API lịch sử trả URL ba ảnh từ kết quả thực tế. |
| D2 | Adapter lưu ảnh | Backend lưu ảnh gốc và hai ảnh XAI qua ImageKit. Có adapter Supabase Storage làm phương án dự phòng. Bản Render đang dùng ImageKit. |
| D3 | Kết nối Supabase | Backend đọc và ghi lịch sử vào bảng `prediction_logs`. Đã đọc danh sách và chi tiết trên dịch vụ Render. |
| D4 | Cấu trúc bản ghi | Bản ghi lưu kết quả, ngưỡng, trạng thái, URL ảnh và metadata. Thời gian xử lý và hai lớp đứng đầu được lưu trong `metadata.processing_time_ms` và `metadata.top_predictions` trên cột JSON hiện có. Kiểm thử xác nhận đọc được bản ghi cũ thiếu hai lớp đứng đầu. |
| D5 | Thống kê theo lô | API trả số ảnh đã xử lý, đang chờ, thành công và lỗi, cùng tỷ lệ hoàn thành. Kết quả hợp lệ được lưu theo từng ảnh. |
| D6 | Chỉ mục và tìm kiếm | SQL trong kế hoạch định nghĩa chỉ mục theo `created_at`, `waste_type` và `pipeline_type`. Adapter tìm tên ảnh bằng `ILIKE`. Sự tồn tại của các chỉ mục trên Supabase chưa được kiểm tra trực tiếp trong lượt rà soát này. |
| D7 | Lỗi dịch vụ phụ thuộc | Backend dò Supabase và kho ảnh theo chu kỳ mặc định 30 giây. Kiểm thử local xác nhận API trả 503 khi thiếu cấu hình cloud và báo lỗi riêng từng ảnh trong lô. |
| D8 | Xóa đồng bộ Supabase → ImageKit | Đã cài SQL trên Supabase, xác nhận RPC và token trả HTTP 204 với ID không tồn tại. Backend đã triển khai trên Render tại commit `b225567`, trạng thái live, health healthy, Supabase connected và ImageKit reachable. Có 9 kiểm thử Python cùng kiểm thử PostgreSQL local về trigger, rollback, quyền, thời hạn giữ việc và thử lại. Đã tìm đúng ba tệp từ một bản ghi thật bằng kiểm tra chỉ đọc; chưa dùng lịch sử thật làm phép thử xóa. Xem [hướng dẫn](docs/IMAGEKIT_CLEANUP.md). |

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
| F11 | Thử với ảnh mẫu | Có năm ảnh trong tab **Một ảnh**. Kiểm thử trình duyệt xác nhận ảnh được đưa vào khung xem trước và API chỉ được gọi khi bấm dự đoán. Cả năm ảnh đã chạy qua API local với ONNX thật và tạo được hai ảnh XAI. |
| F12 | Xuất CSV lượt xử lý nhiều ảnh | Kiểm thử trình duyệt tải được CSV UTF-8 tạo từ toàn bộ ảnh có kết quả hoặc lỗi trong lượt, kể cả dòng đang bị ẩn bởi bộ lọc. Tệp giữ dấu tiếng Việt, thoát dấu ngoặc kép và vô hiệu hóa chuỗi giống công thức. |
| F13 | Bảng số liệu theo khoảng ngày | Bảng **Xem số liệu theo ngày** có hai ô ngày và phân trang 5 ngày. Bộ chọn khoảng ngày độc lập với các biểu đồ. Kiểm thử trình duyệt đã qua cho trang đầu, trang giữa, trang cuối, lỗi tải và đổi khoảng ngày về trang 1. |
| F14 | Hai lớp có xác suất cao nhất | API trả hai lớp xếp theo xác suất và lưu vào metadata. Giao diện hiện chênh lệch theo điểm phần trăm và lý do chưa đạt ngưỡng trong luồng Thủ công. Ảnh tình huống cho kết quả Nhựa 61,19%, Thủy tinh 35,45%, biên 25,73 điểm phần trăm. Hai chốt đều chưa đạt. |
| F15 | Chụp ảnh từ điện thoại | Nút **Chụp ảnh** yêu cầu camera sau trên thiết bị hỗ trợ. Kiểm thử Chromium mô phỏng điện thoại 390 × 844 px xác nhận đầu vào camera, chuyển ảnh thử 4100 × 4100 sang JPEG 3200 × 3200 và hiển thị xem trước. Bước mở camera và chụp trên điện thoại thật còn cần kiểm tra. [HTML Media Capture](https://www.w3.org/TR/html-media-capture/#the-capture-attribute) |
| F16 | Thống kê bằng biểu đồ | Phần **Thống kê** mặc định đóng, mũi tên hướng lên. Mỗi lần mở bằng nút mũi tên, bộ lọc bắt đầu ở **Hôm nay**. Đã tăng nhẹ chữ trong nội dung và bỏ dòng khoảng thời gian cạnh bộ lọc. Bố cục desktop 2 × 2, dùng chung bộ lọc **Hôm nay / 1 tuần / 1 tháng / 3 tháng**. Hôm nay có trục 00h–23h, chỉ vẽ đến giờ hiện tại. Donut dùng bốn màu riêng và tổng ở giữa. Ô cuối mô tả đặc điểm bốn loại rác. Kiểm thử trình duyệt đã xác nhận trạng thái đóng/mở, chiều mũi tên và bố cục rộng 390 px. |
| F17 | Ba thẻ tổng quan dự đoán | Đã thêm ba thẻ tổng số ảnh, số ảnh phân loại tự động và số ảnh phân loại thủ công phía trên các biểu đồ. Màu nền xanh dương, xanh lá và vàng nhạt. Kiểm thử trình duyệt xác nhận cùng cập nhật theo cả bốn bộ lọc, xếp thành hàng trên desktop và xếp dọc ở chiều rộng 390 px. |

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
- Kiểm thử năm chức năng bổ sung chạy local. Kiểm thử API dùng mô hình ONNX thật, giả lập ImageKit và Supabase. Kịch bản trình duyệt dùng API giả lập. Các chức năng bổ sung đã được triển khai trên Vercel và Render tại commit `2fc2478` ngày 18/11/2026. Kiểm tra production chỉ đọc xác nhận giao diện mới trên Vercel, backend healthy, bốn bộ lọc Hôm nay/tuần/tháng/3 tháng và phân trang 5 ngày hoạt động.
- Biểu đồ dùng 7 và 30 ngày với các mốc theo ngày, 90 ngày với các mốc theo tuần. Ngày có 0 ảnh vẫn xuất hiện trong chuỗi. Bản ghi Chưa thẩm định được tính vào tổng ảnh; ba thẻ chỉ hiển thị tổng số ảnh, Tự động và Thủ công. Hai cột so sánh chỉ thể hiện Tự động và Cần kiểm tra. Build Next.js cùng kiểm thử API và trình duyệt đã qua cho phần biểu đồ.
- Lưới biểu đồ giữ bố cục trong lúc đổi bộ lọc và khi dữ liệu trống. Trên màn hình nhỏ, bốn ô xếp dọc, biểu đồ thời gian hỗ trợ cuộn ngang và donut vừa chiều rộng ô. Tổng và tỷ trọng donut tính trên bốn loại đang hiển thị. Tooltip của hai biểu đồ thời gian dùng tổng ảnh của cả khoảng, bao gồm các bản ghi Chưa thẩm định.
- Bộ lọc Hôm nay giữ 24 giờ trên trục. Các giờ đã qua và không có ảnh hiển thị 0, các giờ chưa tới để trống. Ba thẻ tổng quan tính trực tiếp từ cùng dữ liệu của biểu đồ. Kiểm thử local dùng API Supabase giả lập và dữ liệu trình duyệt giả lập, build Next.js đã qua.
- Sau khi gộp thành phần **Thống kê**, build Next.js và kiểm thử trình duyệt đã qua. Biểu đồ tải khi mở phần Thống kê. Đã kiểm tra bộ lọc Hôm nay, ba thẻ, tooltip và giao diện rộng 390 px sau khi tăng cỡ chữ.
- Bảng số liệu theo ngày đã được kiểm tra trên backend local và Supabase thật cho khoảng 01/11–16/11/2026. Trang 1 và 2 trả 5 ngày, trang 4 trả ngày 16/11. Đã xác nhận trên trình duyệt local việc chọn khoảng ngày, chuyển trang và đóng/mở Thống kê. Khai báo tham số dùng một model truy vấn để tương thích với phiên bản FastAPI local.
- Dọn các cache Python, ảnh chụp kiểm thử có thể tạo lại và gói nén triển khai Uppcoder cũ. Giữ các thư mục dữ liệu `data/datasets`, `data/splits`, `data/zips`, checkpoint và kết quả thí nghiệm.

Các ảnh mẫu lấy từ tập kiểm thử `MyTrashNet_Test_10Percent`. Độ tin cậy trong bảng là xác suất lớp đứng đầu do ONNX trả về trong lượt kiểm thử local.

| Ảnh mẫu | Kết quả dự đoán | Độ tin cậy | Luồng |
| --- | --- | ---: | --- |
| Nhựa · `plastic_0291.jpg` | Nhựa | 95,18% | Tự động |
| Giấy · `paper_0357.jpg` | Giấy | 96,96% | Tự động |
| Kim loại · `metal_0133.jpg` | Kim loại | 97,88% | Tự động |
| Thủy tinh · `glass_0564.jpg` | Thủy tinh | 97,66% | Tự động |
| Tình huống cần kiểm tra · `glass_0976.jpg` | Nhựa | 61,19% | Thủ công |

## 3. Cách xem dung lượng Render

1. Mở [dịch vụ Render](https://dashboard.render.com/web/srv-dbu73mlckfvc73ba62a0), vào **Metrics → Application Metrics → Memory Usage** và chọn hiển thị giá trị thực. Chọn khoảng thời gian ngắn, thử một ảnh hoặc một lô rồi rê chuột trên biểu đồ để đọc RAM của instance. [Tài liệu Render Metrics](https://render.com/docs/service-metrics#cpu-and-memory-usage)
2. Lần đo qua Render API ngày 18/11/2026 lúc 09:56 giờ Việt Nam ghi nhận **347,49 MiB RAM** trên giới hạn **512 MiB**. Điểm cao nhất của chuỗi mẫu một giờ là **357,02 MiB**, lấy mẫu 60 giây. Mẫu theo phút có thể bỏ qua đỉnh ngắn trong lúc xử lý. Đây là RAM instance Render.
3. **Disk** của Web Service Free là filesystem tạm. API Disk Usage trả về chuỗi rỗng và Dashboard chỉ có biểu đồ Disk Usage cho dịch vụ có lưu trữ bền vững. Trong **Logs**, tìm `RENDER_ONNX` và đọc `filesystem_free_bytes` ở dòng `stage: loaded` sau lần khởi động. Trường này là số byte còn trống trên filesystem chứa thư mục tạm, không phải dung lượng riêng của mã nguồn, mô hình hoặc toàn bộ dịch vụ. [Giới hạn Render Free](https://render.com/docs/free#local-files-lost-on-redeploy)
