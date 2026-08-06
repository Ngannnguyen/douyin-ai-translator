from __future__ import annotations

from pathlib import Path

from .errors import AppError


def is_url(value: str) -> bool:
    return value.lower().startswith(("http://", "https://"))


def obtain_video(source: str, work_dir: Path, progress) -> Path:
    source = source.strip().strip('"')
    if not source:
        raise AppError("IN001")
    if not is_url(source):
        path = Path(source)
        if not path.is_file():
            raise AppError("IN002", source)
        return path.resolve()

    progress(8, "Đang tải video từ liên kết...")
    try:
        import yt_dlp

        output_template = str(work_dir / "video_goc.%(ext)s")
        options = {
            "outtmpl": output_template,
            "format": "bv*+ba/b",
            "merge_output_format": "mp4",
            "noplaylist": True,
            "quiet": True,
            "no_warnings": True,
        }
        with yt_dlp.YoutubeDL(options) as ydl:
            info = ydl.extract_info(source, download=True)
            prepared = Path(ydl.prepare_filename(info))
        candidates = sorted(work_dir.glob("video_goc.*"), key=lambda p: p.stat().st_mtime, reverse=True)
        if prepared.exists():
            return prepared
        if candidates:
            return candidates[0]
        raise FileNotFoundError("Không tìm thấy tệp sau khi tải")
    except Exception as exc:
        raise AppError("DL001", str(exc)) from exc
