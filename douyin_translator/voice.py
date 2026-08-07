from __future__ import annotations

import asyncio
import math
import wave
from pathlib import Path

import numpy as np

from .errors import AppError
from .media import _run
from .speaker import VoiceProfile, emotion_rate, estimate_pitch, read_mono_wav
from .system import get_ffmpeg


FEMALE_VOICE = "vi-VN-HoaiMyNeural"
MALE_VOICE = "vi-VN-NamMinhNeural"
CHILD_VOICE = "vi-VN-child"


def voice_settings(voice: str) -> tuple[str, str, str]:
    if voice == CHILD_VOICE:
        return FEMALE_VOICE, "+8%", "+35Hz"
    if voice not in {FEMALE_VOICE, MALE_VOICE}:
        raise ValueError(f"Giọng đọc không hợp lệ: {voice}")
    return voice, "+0%", "+0Hz"


def _read_mono_wav(audio: Path) -> tuple[np.ndarray, int]:
    return read_mono_wav(audio)


def choose_voice(samples: np.ndarray, sample_rate: int) -> str:
    pitch = estimate_pitch(samples, sample_rate)
    if pitch >= 250:
        return CHILD_VOICE
    return FEMALE_VOICE if pitch >= 165 else MALE_VOICE


def tempo_filters(source_seconds: float, target_seconds: float) -> str:
    # Giọng kể hài hước có thể nhanh hơn nhẹ, nhưng không ép kiểu máy.
    ratio = max(0.92, min(1.20, source_seconds / max(0.25, target_seconds)))
    return f"atempo={ratio:.5f}"


def _percent(value: int) -> str:
    value = max(-12, min(12, int(value)))
    return f"{value:+d}%"


def _pitch(value: int) -> str:
    value = max(-40, min(40, int(value)))
    return f"{value:+d}Hz"


async def _save_tts(
    text: str,
    profile: VoiceProfile,
    output: Path,
    rate_delta: int = 0,
) -> None:
    import edge_tts

    last_error: Exception | None = None
    for attempt in range(3):
        try:
            await edge_tts.Communicate(
                text=text,
                voice=profile.voice,
                rate=_percent(profile.rate_percent + rate_delta),
                pitch=_pitch(profile.pitch_hz),
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


def _decode_mp3(mp3: Path, output: Path) -> Path:
    _run([
        get_ffmpeg(), "-y", "-i", str(mp3), "-ac", "1", "-ar", "24000",
        "-c:a", "pcm_s16le", str(output),
    ], "VOICE001")
    return output


def _fit_decoded_clip(decoded: Path, output: Path, target_seconds: float) -> Path:
    source_seconds = _wav_duration(decoded)
    filters = tempo_filters(source_seconds, target_seconds)
    _run([
        get_ffmpeg(), "-y", "-i", str(decoded), "-af", filters,
        "-ac", "1", "-ar", "24000",
        "-c:a", "pcm_s16le", str(output),
    ], "VOICE001")
    return output


def _validate_timeline_clip(path: Path, target_seconds: float, index: int) -> None:
    """Không cho phép một câu lồng tiếng tràn đáng kể sang câu kế tiếp."""
    actual_seconds = _wav_duration(path)
    allowed_seconds = max(0.65, target_seconds) + 0.08
    if actual_seconds > allowed_seconds:
        raise ValueError(
            f"Câu {index} dài {actual_seconds:.2f} giây, vượt timeline "
            f"{target_seconds:.2f} giây. Hãy rút gọn bản dịch rồi thử lại."
        )


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
        if not translated:
            raise ValueError("Không có lời dịch để tạo giọng Việt")
        output.parent.mkdir(parents=True, exist_ok=True)
        work_dir.mkdir(parents=True, exist_ok=True)
        source_samples, _ = _read_mono_wav(source_audio)
        if not len(source_samples):
            raise ValueError("Âm thanh nguồn rỗng")

        # Một giọng kể cố định, vui tươi và rõ nghĩa. Không đoán nhân vật từ
        # cao độ nữa vì cách đó gán sai khi video dùng một người kể nhiều vai.
        profile = VoiceProfile(0, FEMALE_VOICE, 8, 8)
        translated[:] = [{**item, "speaker_id": 0} for item in translated]
        clips: list[tuple[float, Path]] = []
        total = max(1, len(translated))
        previous_end = 0.0
        for index, segment in enumerate(translated, start=1):
            original_start = max(0.0, float(segment["start"]))
            original_end = max(original_start + 0.65, float(segment["end"]))
            start = max(original_start, previous_end + (0.06 if clips else 0.0))
            target_seconds = original_end - original_start
            text = str(segment["text"]).strip()
            if not text:
                raise ValueError(f"Đoạn lồng tiếng số {index} không có nội dung")

            mp3 = work_dir / f"voice_{index:04}.mp3"
            decoded = work_dir / f"voice_{index:04}_raw.wav"
            wav = work_dir / f"voice_{index:04}.wav"
            asyncio.run(_save_tts(text, profile, mp3, emotion_rate(text)))
            _decode_mp3(mp3, decoded)
            fitted = _fit_decoded_clip(decoded, wav, target_seconds)
            actual_seconds = _wav_duration(fitted)
            segment["start"] = start
            segment["end"] = start + actual_seconds
            previous_end = float(segment["end"])
            clips.append((start, fitted))
            progress(
                76 + int(6 * index / total),
                f"Đang lồng giọng kể vui tươi: câu {index}/{total}",
            )
        duration = max(float(item["end"]) for item in translated) + 0.2
        return _mix_wav_clips(clips, duration, output)
    except AppError:
        raise
    except Exception as exc:
        raise AppError("VOICE001", str(exc)) from exc
