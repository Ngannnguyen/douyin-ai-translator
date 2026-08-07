from __future__ import annotations

from pathlib import Path

from .errors import AppError
from .system import safe_thread_count


def transcribe(audio: Path, model_name: str, progress) -> list[dict]:
    try:
        from faster_whisper import WhisperModel

        progress(28, f"Đang nạp mô hình Whisper {model_name}...")
        model = WhisperModel(
            model_name,
            device="cpu",
            compute_type="int8",
            cpu_threads=safe_thread_count(),
            num_workers=1,
        )
        progress(38, "Đang nhận diện lời nói tiếng Trung...")
        segments, _ = model.transcribe(
            str(audio),
            language="zh",
            vad_filter=True,
            beam_size=1,
        )
        result = [
            {"start": float(item.start), "end": float(item.end), "text": item.text.strip()}
            for item in segments if item.text.strip()
        ]
        if not result:
            raise ValueError("Không phát hiện đoạn hội thoại nào")
        return result
    except Exception as exc:
        raise AppError("AI001", str(exc)) from exc
