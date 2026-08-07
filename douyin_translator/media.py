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
    _run([
        get_ffmpeg(), "-y", "-threads", str(safe_thread_count()),
        "-i", str(video), "-vn", "-ac", "1", "-ar", "16000",
        "-c:a", "pcm_s16le", str(wav_output),
    ], "AU001")
    return wav_output


def extract_audio_mix(video: Path, wav_output: Path) -> Path:
    _run([
        get_ffmpeg(), "-y", "-threads", str(safe_thread_count()),
        "-i", str(video), "-vn", "-ac", "2", "-ar", "44100",
        "-c:a", "pcm_s16le", str(wav_output),
    ], "AU001")
    return wav_output


def _filter_path(path: Path) -> str:
    value = path.resolve().as_posix().replace("'", r"\'")
    if len(value) > 1 and value[1] == ":":
        value = value[0] + r"\:" + value[2:]
    return value


def subtitle_video_filter(subtitle: Path, hide_original: bool = False) -> str:
    # Không làm mờ, không vẽ hộp hoặc thanh đen. Video đầu vào đã được
    # subtitle_removal xóa riêng nét chữ Trung trước khi đến bước này.
    style = (
        "FontName=Arial,FontSize=20,PrimaryColour=&H00FFFFFF,"
        "OutlineColour=&H00000000,BackColour=&H00000000,"
        "BorderStyle=1,Outline=2,Shadow=0,MarginV=30"
    )
    return f"subtitles='{_filter_path(subtitle)}':force_style='{style}'"


def burn_subtitles(
    video: Path,
    subtitle: Path,
    output: Path,
    hide_original: bool = False,
    voice_audio: Path | None = None,
    background_audio: Path | None = None,
) -> Path:
    video_filter = subtitle_video_filter(subtitle, hide_original)
    command = [
        get_ffmpeg(), "-y", "-threads", str(safe_thread_count()),
        "-i", str(video),
    ]
    if voice_audio is not None:
        command += ["-i", str(voice_audio)]
    if background_audio is not None:
        command += ["-i", str(background_audio)]

    if voice_audio is not None:
        command += ["-filter_complex"]
        video_chain = f"[0:v]{video_filter}[v]"
        background_chain = (
            "[2:a]volume=1.0[bg]"
            if background_audio is not None
            else "[0:a]volume=0.35[bg]"
        )
        command += [
            f"{video_chain};{background_chain};[1:a]volume=1.15[voice];"
            "[bg][voice]amix=inputs=2:duration=first:dropout_transition=0[a]",
            "-map", "[v]", "-map", "[a]",
        ]
    else:
        command += ["-vf", video_filter]
    command += [
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
        "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", str(output),
    ]
    _run(command, "VID001")
    return output
