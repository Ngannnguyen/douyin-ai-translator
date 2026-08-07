from __future__ import annotations

import shutil
import tempfile
from dataclasses import dataclass
from pathlib import Path

from .downloader import obtain_video
from .logging_config import configure_logging
from .media import burn_subtitles, extract_audio
from .speech import transcribe
from .subtitles import write_srt
from .system import app_data_dir, choose_model, get_ffmpeg, validate_output_dir, validate_resources
from .translation import translate_segments


@dataclass
class Result:
    video: Path
    subtitle: Path


def unique_path(path: Path) -> Path:
    if not path.exists():
        return path
    for number in range(2, 1000):
        candidate = path.with_name(f"{path.stem}_{number}{path.suffix}")
        if not candidate.exists():
            return candidate
    raise RuntimeError(f"Không thể tạo tên tệp mới cho {path.name}")


def process(source: str, output_dir: Path, progress=lambda percent, message: None) -> Result:
    data_dir = app_data_dir()
    logger = configure_logging(data_dir)
    progress(2, "Đang kiểm tra hệ thống...")
    get_ffmpeg()
    validate_output_dir(output_dir)
    validate_resources()
    work_dir = Path(tempfile.mkdtemp(prefix="job_", dir=data_dir))
    try:
        logger.info("Bắt đầu xử lý nguồn: %s", source)
        video = obtain_video(source, work_dir, progress)
        progress(18, "Đang tách âm thanh...")
        audio = extract_audio(video, work_dir / "am_thanh.wav")
        segments = transcribe(audio, choose_model(), progress)
        translated = translate_segments(segments, progress)
        stem = video.stem[:80] or "video"
        subtitle_temp = write_srt(translated, work_dir / "phu_de_vi.srt")
        progress(82, "Đang chèn phụ đề vào video...")
        rendered_temp = burn_subtitles(video, subtitle_temp, work_dir / "video_tieng_viet.mp4")
        subtitle = unique_path(output_dir / f"{stem}_phu_de_vi.srt")
        output_video = unique_path(output_dir / f"{stem}_tieng_viet.mp4")
        shutil.move(str(subtitle_temp), subtitle)
        shutil.move(str(rendered_temp), output_video)
        progress(100, "Hoàn thành!")
        logger.info("Hoàn thành: %s", output_video)
        return Result(output_video, subtitle)
    except Exception:
        logger.exception("Xử lý thất bại")
        raise
    finally:
        shutil.rmtree(work_dir, ignore_errors=True)
