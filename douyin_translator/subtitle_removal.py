from __future__ import annotations

import os
import subprocess
from pathlib import Path

import numpy as np

from .errors import AppError
from .system import get_ffmpeg, safe_thread_count


def detect_subtitle_mask(frame: np.ndarray, start_ratio: float = 0.55) -> np.ndarray:
    """Tạo mask riêng cho nét phụ đề sáng/màu ở nửa dưới khung hình.

    Chỉ các cụm ký tự xếp thành dòng ngang mới được chọn. Vì vậy quần áo,
    khuôn mặt và toàn bộ dải đáy không bị làm mờ như cách cũ.
    """
    import cv2

    height, width = frame.shape[:2]
    top = max(0, min(height - 1, round(height * start_ratio)))
    roi = frame[top:height]
    hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
    gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)

    # Phụ đề Douyin thường là trắng hoặc vàng, có viền tối.
    white = cv2.inRange(hsv, (0, 0, 165), (180, 145, 255))
    yellow = cv2.inRange(hsv, (10, 80, 135), (45, 255, 255))
    bright = cv2.bitwise_or(white, yellow)

    # Gom các nét chữ gần nhau thành dòng để không nhầm vật thể sáng đơn lẻ.
    join_width = max(5, width // 90)
    grouped = cv2.morphologyEx(
        bright,
        cv2.MORPH_CLOSE,
        cv2.getStructuringElement(cv2.MORPH_RECT, (join_width, 3)),
        iterations=1,
    )
    grouped = cv2.dilate(
        grouped,
        cv2.getStructuringElement(cv2.MORPH_RECT, (join_width, 3)),
        iterations=1,
    )

    candidates = np.zeros_like(bright)
    count, _, stats, _ = cv2.connectedComponentsWithStats(grouped, 8)
    for index in range(1, count):
        x, y, box_width, box_height, area = stats[index]
        if not (max(6, height // 90) <= box_height <= max(20, height // 8)):
            continue
        if box_width < max(35, width // 14):
            continue
        if area < max(40, width // 12):
            continue
        # Dòng chữ thường có mật độ nét vừa phải và nằm trong khung an toàn.
        if x + box_width < width * 0.08 or x > width * 0.92:
            continue
        pad_x = max(3, width // 250)
        pad_y = max(3, height // 250)
        x1, x2 = max(0, x - pad_x), min(width, x + box_width + pad_x)
        y1, y2 = max(0, y - pad_y), min(roi.shape[0], y + box_height + pad_y)
        candidates[y1:y2, x1:x2] = 255

    glyphs = cv2.bitwise_and(bright, candidates)
    # Lấy thêm viền đen sát nét sáng nhưng không tô kín cả hộp chữ.
    edges = cv2.Canny(gray, 45, 150)
    halo = cv2.dilate(glyphs, np.ones((5, 5), np.uint8), iterations=1)
    outlines = cv2.bitwise_and(edges, halo)
    mask_roi = cv2.bitwise_or(glyphs, outlines)
    mask_roi = cv2.dilate(mask_roi, np.ones((3, 3), np.uint8), iterations=2)

    mask = np.zeros((height, width), dtype=np.uint8)
    mask[top:height] = mask_roi
    return mask


def remove_subtitles_from_frame(frame: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Xóa nét chữ bằng tái tạo điểm ảnh lân cận, không tạo thanh mờ."""
    import cv2

    mask = detect_subtitle_mask(frame)
    if not np.any(mask):
        return frame, mask
    cleaned = cv2.inpaint(frame, mask, 4, cv2.INPAINT_TELEA)
    return cleaned, mask


def remove_burned_subtitles(
    video: Path,
    output: Path,
    progress=lambda percent, message: None,
) -> Path:
    """Xóa phụ đề cứng theo từng frame và giữ lại âm thanh gốc."""
    try:
        import cv2

        capture = cv2.VideoCapture(str(video))
        if not capture.isOpened():
            raise RuntimeError("Không mở được video để xóa phụ đề Trung")
        width = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = float(capture.get(cv2.CAP_PROP_FPS) or 25.0)
        total = max(1, int(capture.get(cv2.CAP_PROP_FRAME_COUNT) or 1))
        if width < 16 or height < 16 or fps <= 0:
            raise RuntimeError("Thông số video không hợp lệ")

        output.parent.mkdir(parents=True, exist_ok=True)
        command = [
            get_ffmpeg(), "-y", "-loglevel", "error",
            "-threads", str(safe_thread_count()),
            "-f", "rawvideo", "-pix_fmt", "bgr24",
            "-s", f"{width}x{height}", "-r", f"{fps:.6f}", "-i", "pipe:0",
            "-i", str(video),
            "-map", "0:v:0", "-map", "1:a?",
            "-c:v", "libx264", "-preset", "fast", "-crf", "16",
            "-c:a", "copy", "-shortest", "-movflags", "+faststart", str(output),
        ]
        creationflags = 0
        if os.name == "nt":
            creationflags = subprocess.CREATE_NO_WINDOW | subprocess.BELOW_NORMAL_PRIORITY_CLASS
        process = subprocess.Popen(
            command,
            stdin=subprocess.PIPE,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            creationflags=creationflags,
        )
        assert process.stdin is not None
        frame_index = 0
        try:
            while True:
                ok, frame = capture.read()
                if not ok:
                    break
                cleaned, _ = remove_subtitles_from_frame(frame)
                process.stdin.write(cleaned.tobytes())
                frame_index += 1
                if frame_index % max(1, round(fps)) == 0:
                    progress(
                        82 + int(4 * frame_index / total),
                        f"Đang xóa nét phụ đề Trung: {frame_index}/{total} khung hình",
                    )
        finally:
            capture.release()
            process.stdin.close()
        stderr = (process.stderr.read() if process.stderr else b"").decode("utf-8", "replace")
        code = process.wait(timeout=7200)
        if code != 0:
            raise RuntimeError(stderr[-1500:] or f"FFmpeg kết thúc với mã {code}")
        if not output.is_file() or output.stat().st_size == 0:
            raise RuntimeError("Không tạo được video đã xóa phụ đề Trung")
        return output
    except AppError:
        raise
    except Exception as exc:
        raise AppError("SUBRM001", str(exc)) from exc
