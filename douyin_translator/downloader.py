from __future__ import annotations

import re
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from .errors import AppError


def is_url(value: str) -> bool:
    return value.lower().startswith(("http://", "https://"))


def extract_url(value: str) -> str:
    """Lấy URL đầu tiên khi người dùng dán cả nội dung chia sẻ Douyin."""
    match = re.search(r"https?://[^\s]+", value, flags=re.IGNORECASE)
    if not match:
        return value.strip().strip('"')
    return match.group(0).rstrip(".,;!?)\"'。；！）】")


def normalize_douyin_url(value: str) -> str:
    """Chuyển link trang user/search có modal_id thành link video trực tiếp."""
    source = extract_url(value)
    if not is_url(source):
        return source

    parsed = urlparse(source)
    host = (parsed.hostname or "").lower()
    if host == "douyin.com" or host.endswith(".douyin.com"):
        query = parse_qs(parsed.query)
        video_ids = query.get("modal_id") or query.get("vid") or []
        if video_ids:
            video_id = video_ids[0].strip()
            if video_id.isdigit():
                return f"https://www.douyin.com/video/{video_id}"
    return source


def is_douyin_url(value: str) -> bool:
    if not is_url(value):
        return False
    host = (urlparse(value).hostname or "").lower()
    return host == "douyin.com" or host.endswith(".douyin.com")


def download_options(source: str, output_template: str) -> dict:
    return {
        "outtmpl": output_template,
        "format": "bv*+ba/b",
        "merge_output_format": "mp4",
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
        "socket_timeout": 20,
        "retries": 2,
        "fragment_retries": 2,
    }


def obtain_video(source: str, work_dir: Path, progress) -> Path:
    source = normalize_douyin_url(source)
    if not source:
        raise AppError("IN001")
    if not is_url(source):
        path = Path(source)
        if not path.is_file():
            raise AppError("IN002", source)
        size_gb = path.stat().st_size / (1024 ** 3)
        if size_gb > 2:
            raise AppError("IN003", f"Dung lượng tệp: {size_gb:.2f} GB")
        return path.resolve()

    progress(8, "Đang tải video từ liên kết ở chế độ an toàn...")
    try:
        import yt_dlp

        output_template = str(work_dir / "video_goc.%(ext)s")
        options = download_options(source, output_template)
        with yt_dlp.YoutubeDL(options) as ydl:
            info = ydl.extract_info(source, download=True)
            prepared = Path(ydl.prepare_filename(info))
        candidates = sorted(work_dir.glob("video_goc.*"), key=lambda p: p.stat().st_mtime, reverse=True)
        if prepared.exists():
            return prepared
        if candidates:
            return candidates[0]
        raise FileNotFoundError("Không tìm thấy tệp sau khi tải")
    except AppError:
        raise
    except Exception as exc:
        detail = str(exc)
        if is_douyin_url(source) and "cookie" in detail.lower():
            raise AppError("DL003", detail) from exc
        raise AppError("DL001", str(exc)) from exc
