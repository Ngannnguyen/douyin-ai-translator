from __future__ import annotations

from pathlib import Path

from .errors import AppError


def separate_background(
    source_audio: Path,
    output: Path,
    progress=lambda percent, message: None,
) -> Path:
    """Tách giọng nói khỏi nhạc và âm thanh bối cảnh bằng Demucs."""
    try:
        import torch
        from demucs.api import Separator, save_audio

        device = "cuda" if torch.cuda.is_available() else "cpu"
        progress(82, f"Đang tách thoại Trung khỏi âm thanh nền bằng AI ({device.upper()})...")
        separator = Separator(
            model="mdx_q",
            device=device,
            shifts=0,
            split=True,
            overlap=0.1,
            jobs=1,
            progress=False,
        )
        original, stems = separator.separate_audio_file(str(source_audio))
        vocals = stems.get("vocals")
        if vocals is None:
            raise RuntimeError("Mô hình tách âm thanh không trả về phần vocals")

        # Lấy bản gốc trừ stem lời thoại giúp giữ lại nhạc, hiệu ứng và bối cảnh.
        background = original - vocals
        output.parent.mkdir(parents=True, exist_ok=True)
        save_audio(
            background,
            str(output),
            samplerate=separator.samplerate,
            bits_per_sample=16,
        )
        if not output.is_file() or output.stat().st_size == 0:
            raise RuntimeError("AI không tạo được tệp âm thanh nền")
        return output
    except AppError:
        raise
    except Exception as exc:
        raise AppError("SEP001", str(exc)) from exc
