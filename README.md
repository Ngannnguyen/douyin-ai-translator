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

## Tạo file EXE

Nhấp đúp `TAO_FILE_EXE.bat`. Kết quả nằm trong:

`dist/Douyin_AI_Translator/Douyin_AI_Translator.exe`

Nên dùng chế độ thư mục thay vì `onefile` vì thư viện AI có dung lượng lớn và khởi động chậm.

## Phạm vi Sprint 1

Đã làm: nhập link/file, tải video, nhận diện tiếng Trung, dịch tiếng Việt, tạo SRT, chèn phụ đề, tiến trình nền, kiểm tra Python/FFmpeg/thư viện/dung lượng/quyền ghi và lỗi tiếng Việt.

Chưa làm trong Sprint 1: lồng tiếng Việt, tạo hook/caption, tài khoản, tìm trend tự động và đăng bài đa nền tảng.

## Lưu ý bản quyền

Chỉ xử lý video mà bạn sở hữu hoặc được phép sử dụng. Nền tảng có thể thay đổi cơ chế liên kết; khi tải link lỗi, hãy tải video hợp pháp về máy rồi chọn tệp trực tiếp.
