from __future__ import annotations

import asyncio
import math
import wave
from pathlib import Path

import numpy as np

from .errors import AppError
from .media import _run
from .system import get_ffmpeg


FEMALE_VOICE = "vi-VN-HoaiMyNeural"
MALE_VOICE = "vi-VN-NamMinhNeural"
CHILD_VOICE = "vi-VN-child"


def _read_mono_wav(audio: Path) -> tuple[np.ndarray, int]:
    with wave.open(str(audio), "rb") as source:
        channels = source.getnchannels()
        rate = source.getframerate()
        width = source.getsampwidth()
        if width != 2:
            raise ValueError("Âm thanh phân tích phải là PCM 16-bit")
        samples = np.frombuffer(source.readframes(source.getnframes()), dtype="<i2")
    if channels > 1:
        samples = samples.reshape(-1, channels).mean(axis=1)
    return samples.astype(np.float32) / 32768.0, rate


def estimate_pitch(samples: np.ndarray, sample_rate: int) -> float:
    """Ước lượng cao độ lời nói; trả 0 khi đoạn quá ngắn hoặc không rõ giọng."""
    frame_size = max(256, int(sample_rate * 0.04))
    hop = max(128, frame_size // 2)
    min_lag = max(1, int(sample_rate / 350))
    max_lag = min(frame_size - 2, int(sample_rate / 75))
    pitches: list[float] = []
    for start in range(0, max(0, len(samples) - frame_size), hop):
        frame = samples[start:start + frame_size]
        frame = frame - float(frame.mean())
        energy = float(np.sqrt(np.mean(frame * frame)))
        if energy < 0.01:
            continue
        frame *= np.hanning(len(frame))
        correlation = np.correlate(frame, frame, mode="full")[frame_size - 1:]
        search = correlation[min_lag:max_lag + 1]
        if not len(search) or correlation[0] <= 0:
            continue
        lag = min_lag + int(np.argmax(search))
        if correlation[lag] / correlation[0] >= 0.22:
            pitches.append(sample_rate / lag)
    return float(np.median(pitches)) if pitches else 0.0


def choose_voice(samples: np.ndarray, sample_rate: int) -> str:
    pitch = estimate_pitch(samples, sample_rate)
    if pitch >= 250:
        return CHILD_VOICE
    return FEMALE_VOICE if pitch >= 165 else MALE_VOICE


def tempo_filters(source_seconds: float, target_seconds: float) -> str:
    ratio = max(0.25, min(4.0, source_seconds / max(0.25, target_seconds)))
    factors: list[float] = []
    while ratio > 2.0:
        factors.append(2.0)
        ratio /= 2.0
    while ratio < 0.5:
        factors.append(0.5)
        ratio /= 0.5
    factors.append(ratio)
    return ",".join(f"atempo={factor:.5f}" for factor in factors)


async def _save_tts(text: str, voice: str, output: Path) -> None:
    import edge_tts

    # Edge TTS chưa có giọng trẻ em tiếng Việt riêng. Tạo preset trẻ em từ
    # Hoài My bằng cách tăng cao độ và nhịp nói, sau đó vẫn căn lại timeline.
    edge_voice = FEMALE_VOICE if voice == CHILD_VOICE else voice
    rate = "+12%" if voice == CHILD_VOICE else "+0%"
    pitch = "+35Hz" if voice == CHILD_VOICE else "+0Hz"
    last_error: Exception | None = None
    for attempt in range(3):
        try:
            await edge_tts.Communicate(
                text=text,
                voice=edge_voice,
                rate=rate,
                pitch=pitch,
            ).save(str(output))
            if output.is_file() and output.stat().st_size > 0:
                return
        except Exception as exc:
            last_error = exc
        if attempt < 2:
            await asyncio.sleep(1.5 * (attempt + 1))
    raise RuntimeError(f"Dịch vụ giọng đọc không phản hồi sau 3 lần: {last_error}")


def _wav_duration(path: Path) -> float:
    with wave.open(str(path), "rb") as source:
        return source.getnframes() / max(1, source.getframerate())


def _fit_clip(mp3: Path, output: Path, target_seconds: float) -> Path:
    decoded = output.with_name(output.stem + "_raw.wav")
    _run([get_ffmpeg(), "-y", "-i", str(mp3), "-ac", "1", "-ar", "24000", "-c:a", "pcm_s16le", str(decoded)], "VOICE001")
    filters = tempo_filters(_wav_duration(decoded), target_seconds)
    _run([
        get_ffmpeg(), "-y", "-i", str(decoded), "-af", filters,
        "-t", f"{max(0.25, target_seconds):.3f}", "-ac", "1", "-ar", "24000",
        "-c:a", "pcm_s16le", str(output),
    ], "VOICE001")
    decoded.unlink(missing_ok=True)
    return output


def _mix_wav_clips(clips: list[tuple[float, Path]], duration: float, output: Path) -> Path:
    rate = 24000
    canvas = np.zeros(max(1, math.ceil(duration * rate)), dtype=np.float32)
    for start, clip in clips:
        samples, clip_rate = _read_mono_wav(clip)
        if clip_rate != rate:
            raise ValueError("Tốc độ mẫu giọng đọc không đồng nhất")
        offset = max(0, round(start * rate))
        length = min(len(samples), len(canvas) - offset)
        if length > 0:
            canvas[offset:offset + length] += samples[:length]
    peak = float(np.max(np.abs(canvas))) if len(canvas) else 0.0
    if peak > 0.98:
        canvas *= 0.98 / peak
    pcm = (np.clip(canvas, -1, 1) * 32767).astype("<i2")
    with wave.open(str(output), "wb") as target:
        target.setnchannels(1)
        target.setsampwidth(2)
        target.setframerate(rate)
        target.writeframes(pcm.tobytes())
    return output


def create_vietnamese_voice(
    translated: list[dict],
    source_audio: Path,
    output: Path,
    work_dir: Path,
    progress=lambda percent, message: None,
) -> Path:
    try:
        source_samples, sample_rate = _read_mono_wav(source_audio)
        clips: list[tuple[float, Path]] = []
        total = max(1, len(translated))
        for index, segment in enumerate(translated, start=1):
            start = max(0.0, float(segment["start"]))
            end = max(start + 0.25, float(segment["end"]))
            left = round(start * sample_rate)
            right = round(end * sample_rate)
            voice = choose_voice(source_samples[left:right], sample_rate)
            mp3 = work_dir / f"voice_{index:04}.mp3"
            wav = work_dir / f"voice_{index:04}.wav"
            asyncio.run(_save_tts(str(segment["text"]), voice, mp3))
            _fit_clip(mp3, wav, end - start)
            clips.append((start, wav))
            progress(76 + int(8 * index / total), f"Đang tạo giọng Việt: {index}/{total} đoạn")
        duration = max(float(item["end"]) for item in translated) + 0.5
        return _mix_wav_clips(clips, duration, output)
    except AppError:
        raise
    except Exception as exc:
        raise AppError("VOICE001", str(exc)) from exc
