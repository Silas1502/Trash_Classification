# Frontend phân loại rác

Từ thư mục `frontend/`, chạy với Node.js 20.9 trở lên:

```powershell
npm install
npm run dev
```

Mở [http://localhost:3000](http://localhost:3000). URL mặc định của API là `http://localhost:8000/api/v1`; có thể chỉnh `NEXT_PUBLIC_API_URL` trong `.env.local` rồi khởi động lại Next.js. FastAPI cần cho phép origin `http://localhost:3000` trong `CORS_ORIGINS`. Xem [hướng dẫn backend](../backend/README.md) để khởi động API.

- **Phân loại:** kéo thả hoặc chọn ảnh JPEG, PNG, WebP (tối đa 8 MB/ảnh theo cấu hình hiện tại của backend). Trong tab Nhiều ảnh, kéo cả thư mục từ trình quản lý tệp vào khung tải để đọc cả thư mục con, hoặc dùng nút Chọn nhiều ảnh.
- **Tiến độ:** frontend gửi tối đa 4 ảnh mỗi yêu cầu batch và cập nhật theo từng phản hồi. Nút Dừng hoàn tất lô đang gửi rồi ngừng gửi lô mới; có thể tiếp tục từ ảnh chưa xử lý.
- **Lịch sử:** tìm kiếm, lọc, phân trang, bấm một dòng để mở cửa sổ chi tiết và xuất CSV theo bộ lọc. Ngày giờ dùng múi giờ Việt Nam (UTC+07:00).
- **XAI:** ảnh gốc và Grad-CAM dùng URL API trả về. Với kết quả mô phỏng không có URL, ảnh gốc lấy từ tệp vừa chọn; Grad-CAM cần kết quả thực và dịch vụ lưu trữ.

Kiểm tra với `npm run typecheck` và `npm run build`.
