from __future__ import annotations

import os
import subprocess
from pathlib import Path

from .errors import AppError
from .system import get_ffmpeg, safe_thread_count


def _run(command: list[str], code: str) -> None:
    try:
        creationflags = 0
        if os.name == "nt":
            creationflags = subprocess.CREATE_NO_WINDOW | subprocess.BELOW_NORMAL_PRIORITY_CLASS
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            stdin=subprocess.DEVNULL,
            timeout=7200,
            creationflags=creationflags,
        )
        if result.returncode != 0:
            raise RuntimeError(result.stderr[-1500:])
    except Exception as exc:
        raise AppError(code, str(exc)) from exc


def extract_audio(video: Path, wav_output: Path) -> Path:
    _run([get_ffmpeg(), "-y", "-threads", str(safe_thread_count()), "-i", str(video), "-vn", "-ac", "1", "-ar", "16000", "-c:a", "pcm_s16le", str(wav_output)], "AU001")
    return wav_output


def _filter_path(path: Path) -> str:
    value = path.resolve().as_posix().replace("'", r"\'")
    if len(value) > 1 and value[1] == ":":
        value = value[0] + r"\:" + value[2:]
    return value


def burn_subtitles(video: Path, subtitle: Path, output: Path) -> Path:
    style = "FontName=Arial,FontSize=20,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,BorderStyle=1,Outline=2,Shadow=0,MarginV=28"
    video_filter = f"subtitles='{_filter_path(subtitle)}':force_style='{style}'"
    _run([get_ffmpeg(), "-y", "-threads", str(safe_thread_count()), "-i", str(video), "-vf", video_filter, "-c:v", "libx264", "-preset", "veryfast", "-crf", "22", "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", str(output)], "VID001")
    return output
