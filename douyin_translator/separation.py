from __future__ import annotations

import os
import sys
import wave
from pathlib import Path

import numpy as np

from .errors import AppError


_AI_SINKS: list[object] = []


def ensure_writable_standard_streams() -> None:
    """Khôi phục stdout/stderr bị PyInstaller --windowed đặt thành None.

    Torch/Demucs/tqdm ghi tiến độ tải model vào các luồng này. Nếu chúng là
    None, lần tải model đầu tiên sẽ lỗi: 'NoneType' object has no attribute
    'write'. Giữ sink mở suốt vòng đời ứng dụng để thư viện không ghi vào
    file đã đóng.
    """
    for name in ("stdout", "stderr"):
        stream = getattr(sys, name, None)
        if stream is None or not callable(getattr(stream, "write", None)):
            sink = open(os.devnull, "w", encoding="utf-8", buffering=1)
            setattr(sys, name, sink)
            _AI_SINKS.append(sink)


def separate_background(
    source_audio: Path,
    output: Path,
    progress=lambda percent, message: None,
) -> Path:
    """Tách giọng nói khỏi nhạc và âm thanh bối cảnh bằng Demucs."""
    try:
        # Chạy trước khi import torch/demucs vì tqdm có thể chụp stderr
        # ngay trong quá trình import hoặc tải model lần đầu.
        ensure_writable_standard_streams()

        import torch
        from demucs.apply import apply_model
        from demucs.audio import convert_audio
        from demucs.pretrained import get_model

        device = "cuda" if torch.cuda.is_available() else "cpu"
        progress(82, f"Đang tách thoại Trung khỏi âm thanh nền bằng AI ({device.upper()})...")
        # Demucs 4.0.1 khong co demucs.api. Dung cung API noi bo ma lenh
        # `python -m demucs` cua chinh thu vien su dung de tuong thich ban EXE.
        # htdemucs la model chuan khong nen, khong can goi `diffq` nhu mdx_q.
        # Nhờ vậy bản Windows không phụ thuộc gói biên dịch thêm và ổn định hơn.
        model = get_model("htdemucs")
        model.to(device)
        model.eval()

        # `source_audio` do ung dung tao ra luon la PCM 16-bit. Doc truc tiep
        # de khong phu thuoc ffprobe/codec cua Windows trong ban dong goi.
        with wave.open(str(source_audio), "rb") as source:
            sample_rate = source.getframerate()
            channels = source.getnchannels()
            if source.getsampwidth() != 2:
                raise RuntimeError("Âm thanh nguồn phải là PCM 16-bit")
            pcm = np.frombuffer(source.readframes(source.getnframes()), dtype="<i2")
        if channels < 1 or not len(pcm) or len(pcm) % channels:
            raise RuntimeError("Âm thanh nguồn rỗng hoặc sai cấu trúc kênh")
        wav = torch.from_numpy(pcm.copy()).float().view(-1, channels).t() / 32768.0
        wav = convert_audio(wav, sample_rate, model.samplerate, model.audio_channels)
        reference = wav.mean(0)
        mean = reference.mean()
        std = reference.std().clamp_min(1e-8)
        normalized = (wav - mean) / std

        def run_model(selected_device: str):
            with torch.inference_mode():
                return apply_model(
                    model,
                    normalized[None],
                    device=selected_device,
                    shifts=0,
                    split=True,
                    overlap=0.1,
                    progress=False,
                    num_workers=0,
                )[0]

        try:
            sources = run_model(device)
        except RuntimeError as gpu_error:
            if device != "cuda" or "cuda" not in str(gpu_error).lower():
                raise
            # RTX vẫn có thể hết VRAM với video dài. Tự chuyển sang CPU thay
            # vì làm hỏng toàn bộ công việc đã nhận diện và dịch trước đó.
            progress(82, "GPU không đủ bộ nhớ; đang tự chuyển tách thoại sang CPU...")
            torch.cuda.empty_cache()
            model.to("cpu")
            sources = run_model("cpu")
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
        pcm_output = (
            background.clamp(-1, 1).t().contiguous().cpu().numpy() * 32767
        ).astype("<i2")
        with wave.open(str(output), "wb") as target:
            target.setnchannels(background.shape[0])
            target.setsampwidth(2)
            target.setframerate(model.samplerate)
            target.writeframes(pcm_output.tobytes())
        if not output.is_file() or output.stat().st_size == 0:
            raise RuntimeError("AI không tạo được tệp âm thanh nền")
        return output
    except AppError:
        raise
    except Exception as exc:
        raise AppError("SEP001", str(exc)) from exc

