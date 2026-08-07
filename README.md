# Douyin AI Translator v0.6.4 — Sprint 2

Ứng dụng Windows hỗ trợ:

1. Chọn video có sẵn hoặc dán liên kết video.
2. Nhận diện lời nói tiếng Trung bằng Whisper.
3. Dịch sang tiếng Việt.
4. Tạo tệp phụ đề `.srt`.
5. Chèn phụ đề vào video và xuất tệp `.mp4`.
6. Xóa riêng nét phụ đề Trung bằng tái tạo nền rồi chèn phụ đề Việt; không làm mờ hoặc phủ cả thanh đáy.
7. Nhận diện người nói và khóa một giọng Việt cố định cho từng nhân vật trong toàn bộ video.
8. Tự rút gọn câu dịch dài theo ý chính để lồng tiếng tự nhiên, không ép đọc nhanh như máy.

Mọi lỗi chính đều được hiển thị bằng tiếng Việt, gồm nguyên nhân và hướng xử lý.

Phiên bản 0.6.4 xử lý được câu cực ngắn khoảng một giây: nếu chỉ còn một từ,
ứng dụng tự căn lại âm thanh thay vì hủy toàn bộ video vì không thể rút gọn tiếp.

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

## Hai chế độ lồng tiếng v0.5.1

### 1. Song ngữ

- Giữ tiếng nói, nhạc và âm thanh bối cảnh Trung Quốc.
- Hạ âm lượng nguồn còn 35% để giọng Việt nổi rõ.
- Lồng thêm giọng Việt theo từng đoạn thời gian.

### 2. Thay thoại

- Dùng Demucs AI tách phần lời thoại khỏi nhạc và âm thanh bối cảnh.
- Loại phần thoại Trung đã tách và giữ lại bản nền.
- Lồng giọng Việt lên bản nền theo đúng timeline.
- Lần dùng đầu cần mạng để tải mô hình tách giọng; bước này chậm hơn chế độ 1.

Có thể chọn xóa phụ đề Trung đã gắn cứng trong video. Ứng dụng chỉ tạo mask quanh nét chữ và tái tạo nền tại đúng vùng đó, không làm mờ hoặc phủ đen cả dải đáy.

### Giọng cố định theo nhân vật

- Ứng dụng phân nhóm người nói từ âm thanh gốc và cấp một mã nhân vật.
- Mỗi mã nhân vật giữ nguyên loại giọng Việt trong toàn bộ video.
- Chỉ cảm xúc và tốc độ được điều chỉnh nhẹ; không đổi qua lại giữa giọng nam và nữ.
- Câu dài được rút gọn theo ý tương đương trước khi tạo giọng, tốc độ đọc luôn nằm trong giới hạn tự nhiên.

### Khi tải video Douyin

- Bản v0.4.1 không đọc hồ sơ hoặc cơ sở dữ liệu cookie của Chrome/Edge cá nhân.
- Liên kết công khai vẫn được thử tải trực tiếp với thời gian chờ và số lần thử giới hạn.
- Nếu Douyin yêu cầu cookie, ứng dụng mở một hồ sơ trình duyệt tạm riêng, lấy cookie của đúng phiên đó qua cổng nội bộ rồi tải lại.
- Khi cửa sổ riêng xuất hiện, không cần đăng nhập và không đóng cửa sổ. Ứng dụng sẽ tự đóng ngay sau khi lấy được phiên; chỉ hoàn tất xác minh nếu Douyin thực sự yêu cầu.
- Ứng dụng chỉ đóng cửa sổ tạm do chính nó tạo, không tắt Chrome/Edge đang dùng và không thay đổi cài đặt Windows.
- v0.4.1 theo dõi trực tiếp cổng DevTools của cửa sổ riêng, không còn nhầm việc tiến trình khởi động Chrome kết thúc là người dùng đã đóng cửa sổ.

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

## Phạm vi hiện tại

Đã làm: nhập link/file, tải video, nhận diện tiếng Trung, dịch tiếng Việt, tạo SRT, chèn phụ đề, tiến trình nền, kiểm tra Python/FFmpeg/thư viện/dung lượng/quyền ghi và lỗi tiếng Việt.

Chưa làm: clone chính xác giọng từng nhân vật, lip-sync khẩu hình, tạo hook/caption, tài khoản, tìm trend tự động và đăng bài đa nền tảng.

## Lưu ý bản quyền

Chỉ xử lý video mà bạn sở hữu hoặc được phép sử dụng. Nền tảng có thể thay đổi cơ chế liên kết; khi tải link lỗi, hãy tải video hợp pháp về máy rồi chọn tệp trực tiếp.
