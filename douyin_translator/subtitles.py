from __future__ import annotations

from pathlib import Path

from .errors import AppError


def srt_time(seconds: float) -> str:
    milliseconds = max(0, round(seconds * 1000))
    hours, remainder = divmod(milliseconds, 3_600_000)
    minutes, remainder = divmod(remainder, 60_000)
    secs, millis = divmod(remainder, 1000)
    return f"{hours:02}:{minutes:02}:{secs:02},{millis:03}"


def write_srt(segments: list[dict], output: Path) -> Path:
    try:
        blocks = []
        for index, segment in enumerate(segments, start=1):
            text = str(segment["text"]).replace("\n", " ").strip()
            blocks.append(f"{index}\n{srt_time(segment['start'])} --> {srt_time(segment['end'])}\n{text}")
        output.write_text("\n\n".join(blocks) + "\n", encoding="utf-8-sig")
        return output
    except Exception as exc:
        raise AppError("SUB001", str(exc)) from exc
