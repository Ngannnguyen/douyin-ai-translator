# Douyin AI Translator — Sprint 1

Ứng dụng Windows hỗ trợ:

1. Chọn video có sẵn hoặc dán liên kết video.
2. Nhận diện lời nói tiếng Trung bằng Whisper.
3. Dịch sang tiếng Việt.
4. Tạo tệp phụ đề `.srt`.
5. Chèn phụ đề vào video và xuất tệp `.mp4`.

Mọi lỗi chính đều được hiển thị bằng tiếng Việt, gồm nguyên nhân và hướng xử lý.

## Yêu cầu

- Windows 10 hoặc Windows 11, 64-bit.
- Python 3.11 (chỉ cần khi chạy mã nguồn hoặc tự tạo file EXE).
- Kết nối Internet để tải video, tải mô hình lần đầu và dịch nội dung.
- Tối thiểu 4 GB RAM, khuyến nghị 8 GB.

FFmpeg được cài tự động cùng gói Python `imageio-ffmpeg`, không bắt buộc cài riêng.

## Chạy nhanh trên Windows

1. Giải nén thư mục.
2. Nhấp đúp `CAI_DAT.bat` và chờ cài xong.
3. Có thể chạy `KIEM_TRA_MAY.bat` để kiểm tra máy trước.
4. Nhấp đúp `CHAY_UNG_DUNG.bat`.
5. Chọn video hoặc dán liên kết, sau đó bấm **DỊCH VIDEO**.

Lần chạy nhận diện đầu tiên sẽ tải mô hình Whisper nên lâu hơn bình thường.

### Khi tải video Douyin

- Bản v0.3.0 chạy ở chế độ an toàn: không đọc cookie và không yêu cầu đóng Chrome hoặc Edge.
- Liên kết công khai vẫn được thử tải trực tiếp với thời gian chờ và số lần thử giới hạn.
- Nếu Douyin yêu cầu cookie, ứng dụng dừng và hướng dẫn tải video hợp pháp về máy rồi dùng nút **Chọn video**.
- Ứng dụng không tự tắt trình duyệt, không kết thúc tiến trình và không thay đổi cài đặt Windows.

### Giới hạn tài nguyên an toàn

- Whisper dùng tối đa 2 luồng CPU và 1 worker.
- FFmpeg chạy mức ưu tiên thấp trên Windows, tối đa 2 luồng và có thời gian chờ.
- Máy còn dưới 2 GB RAM khả dụng sẽ được cảnh báo và dừng trước khi xử lý.
- Video lớn hơn 2 GB bị từ chối để tránh quá tải.
- Kết quả cũ không bị ghi đè và tệp tạm được dọn sau mỗi lượt xử lý.

## Tạo file EXE

Nhấp đúp `TAO_FILE_EXE.bat`. Kết quả nằm trong:

`dist/Douyin_AI_Translator/Douyin_AI_Translator.exe`

Nên dùng chế độ thư mục thay vì `onefile` vì thư viện AI có dung lượng lớn và khởi động chậm.

## Phạm vi Sprint 1

Đã làm: nhập link/file, tải video, nhận diện tiếng Trung, dịch tiếng Việt, tạo SRT, chèn phụ đề, tiến trình nền, kiểm tra Python/FFmpeg/thư viện/dung lượng/quyền ghi và lỗi tiếng Việt.

Chưa làm trong Sprint 1: lồng tiếng Việt, tạo hook/caption, tài khoản, tìm trend tự động và đăng bài đa nền tảng.

## Lưu ý bản quyền

Chỉ xử lý video mà bạn sở hữu hoặc được phép sử dụng. Nền tảng có thể thay đổi cơ chế liên kết; khi tải link lỗi, hãy tải video hợp pháp về máy rồi chọn tệp trực tiếp.
