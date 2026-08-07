from __future__ import annotations

import shutil
import tempfile
from dataclasses import dataclass
from pathlib import Path

from .downloader import obtain_video
from .logging_config import configure_logging
from .media import burn_subtitles, extract_audio, extract_audio_mix
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


def process(
    source: str,
    output_dir: Path,
    progress=lambda percent, message: None,
    hide_chinese_subtitles: bool = False,
    audio_mode: str = "original",
) -> Result:
    if audio_mode not in {"original", "dual", "replace"}:
        raise ValueError(f"Chế độ âm thanh không hợp lệ: {audio_mode}")
    data_dir = app_data_dir()
    logger = configure_logging(data_dir)
    progress(2, "Đang kiểm tra hệ thống...")
    get_ffmpeg()
    validate_output_dir(output_dir)
    validate_resources(6.0 if audio_mode == "replace" else 2.0)
    work_dir = Path(tempfile.mkdtemp(prefix="job_", dir=data_dir))
    try:
        logger.info("Bắt đầu xử lý nguồn: %s", source)
        video = obtain_video(source, work_dir, progress)
        progress(18, "Đang tách âm thanh...")
        audio = extract_audio(video, work_dir / "am_thanh.wav")
        segments = transcribe(audio, choose_model(), progress)
        translated = translate_segments(segments, progress)
        stem = video.stem[:80] or "video"

        voice_audio = None
        background_audio = None
        if audio_mode in {"dual", "replace"}:
            from .voice import create_vietnamese_voice

            progress(76, "Đang nhận diện nhân vật và tạo giọng Việt cố định...")
            voice_audio = create_vietnamese_voice(
                translated, audio, work_dir / "long_tieng_vi.wav", work_dir, progress
            )
        if audio_mode == "replace":
            from .separation import separate_background

            source_mix = extract_audio_mix(video, work_dir / "am_thanh_stereo.wav")
            background_audio = separate_background(
                source_mix, work_dir / "nhac_va_boi_canh.wav", progress
            )

        # create_vietnamese_voice có thể rút gọn thêm câu theo thời lượng.
        # Vì vậy chỉ tạo SRT sau khi lồng tiếng để chữ và giọng luôn giống nhau.
        subtitle_temp = write_srt(translated, work_dir / "phu_de_vi.srt")
        render_source = video
        if hide_chinese_subtitles:
            from .subtitle_removal import remove_burned_subtitles

            progress(82, "Đang xóa riêng nét phụ đề Trung và tái tạo nền...")
            render_source = remove_burned_subtitles(
                video, work_dir / "video_da_xoa_chu_trung.mp4", progress
            )
        progress(87, "Đang ghi phụ đề Việt và hoàn thiện âm thanh...")
        rendered_temp = burn_subtitles(
            render_source,
            subtitle_temp,
            work_dir / "video_tieng_viet.mp4",
            hide_original=False,
            voice_audio=voice_audio,
            background_audio=background_audio,
        )
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
