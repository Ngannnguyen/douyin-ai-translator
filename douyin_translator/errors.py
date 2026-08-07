from __future__ import annotations

from dataclasses import dataclass


ERRORS = {
    "SYS001": ("Không tìm thấy FFmpeg", "Ứng dụng chưa tải được bộ xử lý video.", "Kiểm tra kết nối Internet, sau đó chạy lại CAI_DAT.bat."),
    "SYS002": ("Máy không đủ dung lượng trống", "Ổ đĩa lưu kết quả còn dưới 2 GB.", "Dọn bớt dữ liệu hoặc chọn thư mục kết quả ở ổ đĩa khác."),
    "SYS003": ("Không thể ghi tệp kết quả", "Thư mục lưu đang bị khóa hoặc tài khoản Windows không có quyền ghi.", "Chọn thư mục khác, ví dụ thư mục Videos của bạn."),
    "SYS004": ("Thiếu thư viện của ứng dụng", "Quá trình cài đặt chưa hoàn chỉnh hoặc một thư viện bị xóa.", "Chạy lại CAI_DAT.bat và chờ đến khi có thông báo cài đặt thành công."),
    "IN001": ("Nguồn video không hợp lệ", "Bạn chưa chọn tệp video hoặc nhập liên kết.", "Chọn video trong máy hoặc dán một liên kết hợp lệ."),
    "IN002": ("Không tìm thấy video", "Tệp video đã bị di chuyển, đổi tên hoặc xóa.", "Chọn lại đúng tệp video trên máy."),
    "IN003": ("Video vượt giới hạn an toàn", "Tệp video lớn hơn 2 GB và có thể làm máy quá tải trong bản hiện tại.", "Hãy chọn video ngắn hơn hoặc chia video thành các phần nhỏ trước khi xử lý."),
    "DL001": ("Không tải được video", "Liên kết có thể sai, riêng tư, hết hạn hoặc nền tảng đã thay đổi.", "Kiểm tra liên kết; nếu vẫn lỗi, hãy tải video hợp pháp về máy rồi chọn tệp trực tiếp."),
    "DL003": ("Douyin chặn tải trực tiếp", "Douyin yêu cầu một phiên truy cập mới.", "Ứng dụng sẽ tự mở một cửa sổ Douyin riêng và không đọc dữ liệu Chrome/Edge cá nhân."),
    "DL004": ("Không tạo được phiên Douyin an toàn", "Cửa sổ Douyin riêng không tạo được cookie cần thiết hoặc Douyin tiếp tục chặn tải.", "Giữ cửa sổ Douyin riêng mở; nếu có xác minh, hãy hoàn tất trong cửa sổ đó rồi chờ ứng dụng tải lại."),
    "SYS005": ("Máy đang thiếu bộ nhớ khả dụng", "Dung lượng RAM còn trống quá thấp để chạy nhận diện an toàn.", "Đóng bớt ứng dụng nặng, khởi động lại máy và thử lại; phần mềm sẽ không tự tắt ứng dụng khác."),
    "AU001": ("Không tách được âm thanh", "Video hỏng, không có luồng âm thanh hoặc định dạng chưa được hỗ trợ.", "Thử mở video để kiểm tra hoặc chuyển video sang MP4 rồi chạy lại."),
    "AI001": ("Không nhận diện được tiếng nói", "Video có thể không có lời nói, âm quá nhỏ hoặc mô hình AI chưa tải xong.", "Kiểm tra âm thanh, kết nối Internet và thử lại với mô hình nhỏ hơn."),
    "TR001": ("Không dịch được nội dung", "Dịch vụ dịch đang gián đoạn hoặc mất kết nối Internet.", "Kiểm tra mạng rồi thử lại sau ít phút."),
    "SUB001": ("Không tạo được phụ đề", "Dữ liệu thời gian hoặc nội dung nhận diện không hợp lệ.", "Thử lại với video khác và gửi tệp nhật ký nếu lỗi lặp lại."),
    "VID001": ("Không chèn được phụ đề", "Video, phụ đề hoặc bộ mã hóa video gặp lỗi.", "Đảm bảo ổ đĩa còn trống và đường dẫn xuất có quyền ghi."),
    "UNK001": ("Đã xảy ra lỗi chưa xác định", "Ứng dụng gặp lỗi ngoài dự kiến.", "Thử lại; nếu lỗi lặp lại, gửi tệp logs/app.log để kiểm tra."),
}


@dataclass
class AppError(Exception):
    code: str
    technical_detail: str = ""

    def __post_init__(self) -> None:
        super().__init__(self.user_message)

    @property
    def user_message(self) -> str:
        title, message, solution = ERRORS.get(self.code, ERRORS["UNK001"])
        detail = f"\n\nChi tiết kỹ thuật: {self.technical_detail}" if self.technical_detail else ""
        return f"[{self.code}] {title}\n\nNguyên nhân: {message}\n\nCách xử lý: {solution}{detail}"


def convert_error(error: Exception, fallback_code: str = "UNK001") -> AppError:
    if isinstance(error, AppError):
        return error
    return AppError(fallback_code, str(error))
