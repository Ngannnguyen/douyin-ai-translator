from __future__ import annotations

import os
import subprocess
import tempfile
from pathlib import Path

from . import __version__
from .downloader import download_options
from .media import burn_subtitles, extract_audio
from .subtitles import write_srt
from .system import get_ffmpeg, memory_info_gb, safe_thread_count


def _create_sample_video(output: Path) -> None:
    command = [
        get_ffmpeg(), "-y",
        "-f", "lavfi", "-i", "color=c=blue:s=640x360:d=2",
        "-f", "lavfi", "-i", "sine=frequency=440:duration=2",
        "-shortest", "-threads", "2",
        "-c:v", "libx264", "-preset", "ultrafast",
        "-c:a", "aac", str(output),
    ]
    result = subprocess.run(command, capture_output=True, timeout=90)
    if result.returncode != 0 or not output.is_file():
        raise RuntimeError("Không tạo được video kiểm thử")


def run_self_test(report_path: Path | None = None, full: bool = False) -> int:
    report_path = report_path or Path.cwd() / "SELF_TEST_OK.txt"
    try:
        options = download_options("https://www.douyin.com/video/123", "video.%(ext)s")
        if "cookiesfrombrowser" in options or "cookiefile" in options:
            raise RuntimeError("Chế độ an toàn vẫn còn đọc cookie trình duyệt")

        total_gb, available_gb = memory_info_gb()
        full_results: list[str] = []
        with tempfile.TemporaryDirectory(prefix="douyin_self_test_") as folder:
            root = Path(folder)
            source = root / "sample.mp4"
            audio = root / "sample.wav"
            subtitle = root / "sample.srt"
            rendered = root / "rendered.mp4"
            _create_sample_video(source)
            extract_audio(source, audio)
            write_srt(
                [{"start": 0.1, "end": 1.5, "text": "Kiểm tra phụ đề tiếng Việt"}],
                subtitle,
            )
            burn_subtitles(source, subtitle, rendered)
            for path in (source, audio, subtitle, rendered):
                if not path.is_file() or path.stat().st_size == 0:
                    raise RuntimeError(f"Tệp kiểm thử không hợp lệ: {path.name}")

            if full:
                from deep_translator import GoogleTranslator
                from faster_whisper import WhisperModel

                model = WhisperModel(
                    "tiny",
                    device="cpu",
                    compute_type="int8",
                    cpu_threads=safe_thread_count(),
                    num_workers=1,
                )
                segments, _ = model.transcribe(
                    str(audio), language="zh", vad_filter=True, beam_size=1
                )
                list(segments)
                full_results.append("Whisper tiny: DAT")

                translated = GoogleTranslator(source="zh-CN", target="vi").translate("你好")
                if not translated or not translated.strip():
                    raise RuntimeError("Dịch vụ dịch trả về kết quả rỗng")
                full_results.append("Dich Trung-Viet: DAT")

                e2e_url = os.getenv("DOUYIN_E2E_URL", "").strip()
                if e2e_url:
                    from .pipeline import process

                    e2e_output = root / "douyin_e2e_output"
                    e2e_result = process(e2e_url, e2e_output)
                    for path in (e2e_result.video, e2e_result.subtitle):
                        if not path.is_file() or path.stat().st_size == 0:
                            raise RuntimeError(f"E2E Douyin không tạo được {path.name}")
                    subtitle_text = e2e_result.subtitle.read_text(encoding="utf-8-sig")
                    if " --> " not in subtitle_text or len(subtitle_text.strip()) < 20:
                        raise RuntimeError("E2E Douyin tạo phụ đề rỗng hoặc không đúng định dạng SRT")
                    full_results.append("Tai video Douyin that: DAT")
                    full_results.append("Phu de video Douyin that: DAT")

        report_path.write_text(
            "\n".join([
                "SELF TEST: DAT",
                f"Phien ban: {__version__}",
                "Cookie trinh duyet: KHONG DOC",
                "FFmpeg va phu de: DAT",
                f"So luong CPU toi da: {safe_thread_count()}",
                f"RAM: tong {total_gb:.1f} GB, kha dung {available_gb:.1f} GB",
                *full_results,
            ]),
            encoding="utf-8",
        )
        return 0
    except Exception as exc:
        report_path.write_text(f"SELF TEST: LOI\n{exc}", encoding="utf-8")
        return 1
