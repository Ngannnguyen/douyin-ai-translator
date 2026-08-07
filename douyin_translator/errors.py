from __future__ import annotations

from dataclasses import dataclass


ERRORS = {
    "SYS001": ("Không tìm thấy FFmpeg", "Ứng dụng chưa tải được bộ xử lý video.", "Kiểm tra kết nối Internet rồi thử lại."),
    "SYS002": ("Máy không đủ dung lượng trống", "Ổ đĩa lưu kết quả còn quá ít dung lượng.", "Dọn bớt dữ liệu hoặc chọn ổ đĩa khác."),
    "SYS003": ("Không thể ghi tệp kết quả", "Thư mục lưu bị khóa hoặc không có quyền ghi.", "Chọn thư mục Videos hoặc một thư mục khác."),
    "SYS004": ("Thiếu thư viện của ứng dụng", "Quá trình cài đặt chưa hoàn chỉnh.", "Tải lại bản phát hành đầy đủ."),
    "SYS005": ("Máy đang thiếu bộ nhớ khả dụng", "RAM còn trống quá thấp để xử lý an toàn.", "Đóng bớt ứng dụng nặng rồi thử lại."),
    "IN001": ("Nguồn video không hợp lệ", "Bạn chưa chọn video hoặc nhập liên kết.", "Chọn video hoặc dán liên kết hợp lệ."),
    "IN002": ("Không tìm thấy video", "Tệp video đã bị di chuyển hoặc xóa.", "Chọn lại đúng tệp video."),
    "IN003": ("Video vượt giới hạn an toàn", "Video quá lớn với bản hiện tại.", "Chia video thành phần nhỏ hơn."),
    "DL001": ("Không tải được video", "Liên kết sai, riêng tư, hết hạn hoặc nền tảng thay đổi.", "Kiểm tra liên kết hoặc chọn tệp video trong máy."),
    "DL003": ("Douyin chặn tải trực tiếp", "Douyin yêu cầu phiên truy cập mới.", "Ứng dụng sẽ mở cửa sổ Douyin riêng."),
    "DL004": ("Không tạo được phiên Douyin an toàn", "Douyin không tạo cookie cần thiết.", "Giữ cửa sổ Douyin riêng mở và hoàn tất xác minh nếu có."),
    "AU001": ("Không tách được âm thanh", "Video hỏng hoặc không có âm thanh.", "Kiểm tra video rồi thử lại."),
    "AI001": ("Không nhận diện được tiếng nói", "Âm thanh quá nhỏ hoặc mô hình chưa tải xong.", "Kiểm tra mạng và âm thanh."),
    "TR001": ("Không dịch được nội dung", "Dịch vụ dịch gián đoạn hoặc mất mạng.", "Kiểm tra mạng rồi thử lại."),
    "SUB001": ("Không tạo được phụ đề", "Timeline hoặc nội dung không hợp lệ.", "Thử lại và gửi nhật ký nếu lỗi lặp lại."),
    "SUBRM001": ("Không xóa được phụ đề tiếng Trung", "Không đọc được khung hình hoặc bộ tái tạo nền gặp lỗi.", "Kiểm tra dung lượng ổ đĩa; nếu video có chữ ở vị trí đặc biệt, tắt tùy chọn xóa chữ."),
    "VID001": ("Không xuất được video", "Video, phụ đề hoặc bộ mã hóa gặp lỗi.", "Kiểm tra dung lượng và quyền ghi thư mục."),
    "VOICE001": ("Không tạo được giọng lồng tiếng Việt", "Dịch vụ giọng đọc hoặc bước căn thời lượng gặp lỗi.", "Kiểm tra mạng; có thể dùng chế độ không lồng tiếng."),
    "SEP001": ("Không tách được thoại tiếng Trung", "Mô hình tách giọng chưa tải xong, thiếu bộ nhớ hoặc âm thanh không phù hợp.", "Kiểm tra mạng và thử lại; lỗi tải mô hình trong EXE đã có cơ chế tự bảo vệ."),
    "UNK001": ("Đã xảy ra lỗi chưa xác định", "Ứng dụng gặp lỗi ngoài dự kiến.", "Thử lại và gửi logs/app.log."),
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
