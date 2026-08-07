# Tiến độ dự án

## Mốc hiện tại: v0.2.4 — Sprint 1

Ngày cập nhật: 07/08/2026

### Đã hoàn thành

- Giao diện chọn video trong máy hoặc dán liên kết.
- Tải một video bằng `yt-dlp`.
- Tách âm thanh bằng FFmpeg.
- Nhận diện tiếng Trung bằng Faster Whisper.
- Dịch từng đoạn sang tiếng Việt, tự thử lại tối đa 3 lần.
- Tạo phụ đề SRT có BOM UTF-8 để tương thích Windows.
- Chèn phụ đề tiếng Việt vào MP4.
- Xử lý trong luồng nền để giao diện không bị đứng.
- Mã lỗi tiếng Việt gồm nguyên nhân, cách xử lý và chi tiết kỹ thuật.
- Công cụ kiểm tra hệ điều hành, Python 64-bit, thư viện, FFmpeg, dung lượng và quyền ghi.
- Script cài đặt, chạy ứng dụng, kiểm tra máy và tạo EXE trên Windows.
- GitHub Actions build tự động trên máy Windows 64-bit.
- Tự chuyển link trang cá nhân Douyin có `modal_id` hoặc `vid` thành link video trực tiếp.
- Nhận cả đoạn văn bản chia sẻ Douyin và tự lấy URL đầu tiên.
- Dùng cookie Microsoft Edge khi Douyin yêu cầu xác minh, để người dùng vẫn có thể mở Chrome làm việc.
- Thêm mã lỗi DL002 bằng tiếng Việt và hướng dẫn làm mới cookie an toàn.

### Kết quả kiểm tra hiện tại

- Biên dịch toàn bộ mã Python: đạt.
- Kiểm tra định dạng thời gian và tạo SRT tiếng Việt: đạt.
- Kiểm tra đầy đủ nội dung lỗi tiếng Việt: đạt.
- Thử tạo video ngắn và chèn phụ đề qua đường dẫn có dấu/có khoảng trắng: đạt.
- Kiểm tra trực tiếp trên Windows 10/11: chưa thực hiện trong môi trường phát triển hiện tại.
- Kiểm tra tải Douyin và nhận diện một video thực: chưa thực hiện vì chưa có video mẫu được phép sử dụng.

### Phần tiếp theo của Sprint 1

1. Repository đã tạo: `https://github.com/Ngannnguyen/douyin-ai-translator`.
2. Tải gói v0.2.1 lên repository bằng trình duyệt.
3. Theo dõi GitHub Actions build bản Windows 10/11.
4. Tải artifact và kiểm tra mở ứng dụng trên Windows.
5. Chạy thử với một video mẫu ngắn, sửa lỗi và chốt bản Release Candidate.

### Chưa thuộc Sprint 1

- Lồng tiếng Việt.
- Tạo hook, caption và hashtag.
- Tài khoản, gói Free/Pro và thanh toán.
- Tự tìm trend hoặc đăng bài đa nền tảng.

### Trạng thái GitHub khi kết thúc phiên

- Repository tồn tại, công khai và đang trống.
- Người dùng đã kết nối GitHub và chọn repository.
- Phiên hiện tại vẫn chưa nhận được công cụ ghi repository, nên chưa có mã nguồn nào được đẩy lên.
- Không được báo rằng file EXE đã có cho đến khi GitHub Actions build thành công và artifact tải xuống đã được xác minh.
