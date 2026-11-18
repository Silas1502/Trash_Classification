# Xóa ảnh ImageKit khi xóa lịch sử Supabase

**Trạng thái ngày 18/11/2026:** SQL và token đã được xác minh trên Supabase; backend có tác vụ dọn ảnh đã triển khai thành công trên Render tại commit `b225567`. Endpoint health trả `healthy`, database `connected`, storage `reachable`. Các kiểm thử Python/PostgreSQL local đã qua. Chưa dùng lịch sử thật làm phép thử xóa trên cloud.

## Cách hoạt động

1. Khi xóa dòng trong `public.prediction_logs`, trigger ghi ID cùng ba URL ảnh vào hàng đợi riêng trong **cùng giao dịch**. Hủy giao dịch xóa cũng hủy việc thêm vào hàng đợi. SQL có trigger riêng cho thao tác `TRUNCATE`.
2. Khi backend chạy, tác vụ nền lấy tối đa một công việc mỗi lần, tìm đúng `fileId` theo URL và xóa ảnh gốc, Grad-CAM, Spatial Energy. Không tải nội dung ảnh vào RAM và không gọi mô hình dự đoán.
3. Dọn xong thì bỏ công việc khỏi hàng đợi. Khi lỗi, giữ công việc và thử lại sau 1, 2, 4… phút, tối đa 1 giờ giữa hai lần thử. Nếu backend dừng giữa chừng, công việc được lấy lại sau khi hết thời hạn giữ 10 phút.

Backend kiểm tra hàng đợi mỗi **60 giây** theo mặc định, mỗi lượt xử lý tối đa 10 bản ghi. Hàng đợi lớn sẽ cần nhiều lượt. Nếu Render ngủ hoặc dừng, hàng đợi vẫn nằm trong Supabase và được tiếp tục khi backend hoạt động lại.

Chỉ xử lý các URL thuộc ImageKit endpoint đã cấu hình, trong thư mục dự đoán và có UUID trùng bản ghi đã xóa. Các dòng đang tham chiếu cùng ảnh được kiểm tra khi lấy công việc để tránh dọn ảnh còn được sử dụng. Bản ghi cũ chỉ có URL vẫn dùng được, không cần bổ sung `fileId` vào dữ liệu cũ.

## Thiết lập

### 1. Chuẩn bị token và SQL trên máy

Từ thư mục gốc dự án, chạy PowerShell:

```powershell
.\.venv\onnx-runtime\Scripts\python.exe backend\scripts\prepare_imagekit_cleanup.py
```

Lệnh lưu `IMAGEKIT_CLEANUP_TOKEN` trong `backend/.env` và tạo `.venv/imagekit-cleanup-setup.sql`. Hai tệp này được Git bỏ qua. File SQL chứa **mã băm SHA-256** của token; token gốc chỉ nằm ở backend. Chạy lại sẽ giữ token hiện có.

### 2. Cài trigger trên Supabase

Mở **SQL Editor → New query**, dán nội dung `.venv/imagekit-cleanup-setup.sql` và chạy với vai trò `postgres`. Có thể chép SQL bằng PowerShell:

```powershell
Get-Content -LiteralPath '.\.venv\imagekit-cleanup-setup.sql' -Raw | Set-Clipboard
```

SQL tạo schema `imagekit_cleanup`, hàng đợi, trigger và hai RPC có xác thực token. Chạy lại không làm mất hàng đợi. Bước này không xóa lịch sử hay ảnh đang có.

### 3. Kích hoạt backend

Trong Render **Environment**, thêm `IMAGEKIT_CLEANUP_TOKEN` với đúng giá trị trong `backend/.env`; giữ riêng ở backend, không đặt ở Vercel và không gửi khóa qua chat. Các biến Supabase và ImageKit hiện có được dùng lại. Không cần thay khóa publishable hiện tại bằng `service_role`.

Triển khai phiên bản backend có `app/db/imagekit_cleanup.py`. Local cần khởi động lại backend để đọc token mới. Có thể điều chỉnh chu kỳ bằng `IMAGEKIT_CLEANUP_INTERVAL_SECONDS` (mặc định 60).

### 4. Kiểm tra

Tạo một dự đoán thử mới, ghi lại ba đường dẫn ảnh rồi xóa **đúng dòng thử đó** trong Supabase Table Editor. Khi backend đang chạy, đợi khoảng một chu kỳ và kiểm tra ba tệp đã biến mất khỏi ImageKit Media Library. Không dùng dữ liệu cần giữ cho phép thử này.

Xem hàng đợi bằng SQL Editor (không trả token hoặc URL):

```sql
select id, prediction_id, attempts, next_attempt_at, leased_until, last_error
from imagekit_cleanup.jobs
order by id;
```

Hàng đợi trống sau khi xử lý xong. `last_error` chỉ lưu tên loại lỗi. Xem log backend nếu tác vụ chưa truy cập được RPC. Nếu chưa cài SQL hoặc token không khớp, tác vụ sẽ báo lỗi và thử lại, không tự ý xóa ảnh.

## Phạm vi

- Cơ chế có hiệu lực cho các lần xóa **sau khi cài trigger**. Không tự dọn ảnh của những bản ghi đã bị xóa trước đó, ảnh mẫu hay thư mục benchmark.
- Chưa thêm lại nút/API xóa lịch sử trên website. Xóa vẫn thực hiện từ Supabase.
- Xóa file ImageKit là thao tác không thể khôi phục bằng việc chèn lại dòng Supabase. Luôn sao lưu dữ liệu cần giữ trước khi xóa.
- CDN có thể còn bản cache một thời gian dù tệp đã bị xóa khỏi Media Library; thao tác này không gọi API purge cache. [ImageKit SDK: delete file](https://github.com/imagekit-developer/imagekit-python/blob/master/src/imagekitio/resources/files/files.py)
- Không cần Edge Function, cron hoặc dịch vụ trả phí mới.

Tài liệu tham khảo: [Supabase Database Functions](https://supabase.com/docs/guides/database/functions), [PostgreSQL triggers](https://www.postgresql.org/docs/current/trigger-definition.html).
