# Tiến độ dự án

## Mốc hiện tại: v0.4.0 Isolated Douyin Session — Sprint 1

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
- Không đọc hồ sơ hoặc cơ sở dữ liệu cookie Chrome/Edge cá nhân.
- Khi bị Douyin chặn, tự mở một hồ sơ Chrome/Edge tạm qua cổng nội bộ `127.0.0.1`, lấy cookie phiên đó rồi tải lại.
- Không yêu cầu đóng trình duyệt và không can thiệp tiến trình Windows.
- Giới hạn Whisper và FFmpeg ở tối đa 2 luồng CPU; FFmpeg chạy ưu tiên thấp.
- Kiểm tra RAM khả dụng trước khi xử lý và dừng an toàn nếu còn dưới 2 GB.
- Giới hạn video tối đa 2 GB, không ghi đè kết quả cũ và dọn tệp tạm khi lỗi.
- Thêm self-test tạo video mẫu, tách âm thanh và chèn phụ đề ngay trên file EXE Windows.

### Kết quả kiểm tra hiện tại

- Biên dịch toàn bộ mã Python: đạt.
- Kiểm tra định dạng thời gian và tạo SRT tiếng Việt: đạt.
- Kiểm tra đầy đủ nội dung lỗi tiếng Việt: đạt.
- Thử tạo video ngắn và chèn phụ đề qua đường dẫn có dấu/có khoảng trắng: đạt.
- Kiểm tra bản v0.3.0 trực tiếp trên Windows Server 2022: 11 unit test, FFmpeg, Whisper và dịch Trung–Việt đều đạt.
- Bản v0.4.0 sẽ chỉ được phát hành khi GitHub Actions tải được link Douyin mẫu và tạo MP4 + SRT thành công.

### Phần tiếp theo của Sprint 1

1. Đưa mã nguồn v0.4.0 lên repository.
2. Chạy E2E trên Windows với link Douyin mẫu đã cung cấp.
3. Kiểm tra file video tải về, SRT và MP4 đã chèn phụ đề.
4. Chỉ tải artifact và chốt Release Candidate khi tất cả bước đạt.

### Chưa thuộc Sprint 1

- Lồng tiếng Việt.
- Tạo hook, caption và hashtag.
- Tài khoản, gói Free/Pro và thanh toán.
- Tự tìm trend hoặc đăng bài đa nền tảng.

### Trạng thái phát hành

- Repository: `https://github.com/Ngannnguyen/douyin-ai-translator`.
- Bản v0.3.0 đã build và self-test Windows thành công nhưng chưa đạt tải Douyin thật.
- Không phát hành v0.4.0 cho đến khi E2E link Douyin thật đạt.
