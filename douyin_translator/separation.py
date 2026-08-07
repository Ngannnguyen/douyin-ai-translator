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
        from demucs.apply import apply_model
        from demucs.audio import AudioFile, save_audio
        from demucs.pretrained import get_model

        device = "cuda" if torch.cuda.is_available() else "cpu"
        progress(82, f"Đang tách thoại Trung khỏi âm thanh nền bằng AI ({device.upper()})...")
        # Demucs 4.0.1 khong co demucs.api. Dung cung API noi bo ma lenh
        # `python -m demucs` cua chinh thu vien su dung de tuong thich ban EXE.
        model = get_model("mdx_q")
        model.to(device)
        model.eval()

        wav = AudioFile(source_audio).read(
            streams=0,
            samplerate=model.samplerate,
            channels=model.audio_channels,
        )
        reference = wav.mean(0)
        mean = reference.mean()
        std = reference.std().clamp_min(1e-8)
        normalized = (wav - mean) / std

        with torch.inference_mode():
            sources = apply_model(
                model,
                normalized[None],
                device=device,
                shifts=0,
                split=True,
                overlap=0.1,
                progress=False,
                num_workers=0,
            )[0]
        sources = sources * std + mean

        if "vocals" not in model.sources:
            raise RuntimeError("Mô hình tách âm thanh không trả về phần vocals")

        # Cong cac stem khong phai vocals se on dinh hon phep lay ban goc tru
        # vocals va giu lai drums/bass/other (nhac, hieu ung, boi canh).
        background_sources = [
            source for source, name in zip(sources, model.sources) if name != "vocals"
        ]
        if not background_sources:
            raise RuntimeError("Mô hình không trả về âm thanh nền")
        background = torch.stack(background_sources).sum(dim=0)
        output.parent.mkdir(parents=True, exist_ok=True)
        save_audio(
            background,
            str(output),
            samplerate=model.samplerate,
            bits_per_sample=16,
        )
        if not output.is_file() or output.stat().st_size == 0:
            raise RuntimeError("AI không tạo được tệp âm thanh nền")
        return output
    except AppError:
        raise
    except Exception as exc:
        raise AppError("SEP001", str(exc)) from exc
