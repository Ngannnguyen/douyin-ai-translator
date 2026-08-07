from __future__ import annotations

import wave
from dataclasses import dataclass
from pathlib import Path

import numpy as np


@dataclass(frozen=True)
class VoiceProfile:
    speaker_id: int
    voice: str
    rate_percent: int = 0
    pitch_hz: int = 0


def read_mono_wav(audio: Path) -> tuple[np.ndarray, int]:
    with wave.open(str(audio), "rb") as source:
        channels = source.getnchannels()
        rate = source.getframerate()
        if source.getsampwidth() != 2:
            raise ValueError("Âm thanh phân tích phải là PCM 16-bit")
        samples = np.frombuffer(source.readframes(source.getnframes()), dtype="<i2")
    if channels > 1:
        samples = samples.reshape(-1, channels).mean(axis=1)
    return samples.astype(np.float32) / 32768.0, rate


def estimate_pitch(samples: np.ndarray, sample_rate: int) -> float:
    frame_size = max(256, int(sample_rate * 0.04))
    hop = max(128, frame_size // 2)
    min_lag = max(1, int(sample_rate / 350))
    max_lag = min(frame_size - 2, int(sample_rate / 75))
    pitches: list[float] = []
    for start in range(0, max(0, len(samples) - frame_size), hop):
        frame = samples[start:start + frame_size]
        frame = frame - float(frame.mean())
        if float(np.sqrt(np.mean(frame * frame))) < 0.008:
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


def _signature(samples: np.ndarray, sample_rate: int) -> np.ndarray:
    """Dấu vân tay giọng nhẹ: phổ tần + cao độ, không phụ thuộc nội dung câu."""
    if len(samples) < max(1600, sample_rate // 5):
        samples = np.pad(samples, (0, max(1600, sample_rate // 5) - len(samples)))
    samples = samples - float(samples.mean())
    peak = float(np.max(np.abs(samples))) or 1.0
    samples = samples / peak
    window = np.hanning(len(samples))
    spectrum = np.abs(np.fft.rfft(samples * window)) + 1e-7
    frequencies = np.fft.rfftfreq(len(samples), 1.0 / sample_rate)
    bands = []
    edges = np.geomspace(80, min(7000, sample_rate / 2 - 1), 13)
    for left, right in zip(edges[:-1], edges[1:]):
        selected = spectrum[(frequencies >= left) & (frequencies < right)]
        bands.append(float(np.log(selected.mean() + 1e-7)) if len(selected) else -16.0)
    vector = np.asarray(bands, dtype=np.float32)
    vector -= float(vector.mean())
    norm = float(np.linalg.norm(vector)) or 1.0
    return vector / norm


def _cosine(left: np.ndarray, right: np.ndarray) -> float:
    return float(np.dot(left, right) / ((np.linalg.norm(left) * np.linalg.norm(right)) or 1.0))


def assign_speakers(
    segments: list[dict],
    source_audio: Path,
    max_speakers: int = 6,
) -> tuple[list[dict], dict[int, VoiceProfile]]:
    """Gán mã người nói một lần; mọi câu sau dùng lại đúng VoiceProfile đó."""
    if not segments:
        return [], {}
    samples, rate = read_mono_wav(source_audio)
    prototypes: list[np.ndarray] = []
    members: list[list[tuple[np.ndarray, float]]] = []
    assigned: list[dict] = []

    for segment in segments:
        start = max(0, round(float(segment["start"]) * rate))
        end = min(len(samples), round(float(segment["end"]) * rate))
        clip = samples[start:end]
        signature = _signature(clip, rate)
        pitch = estimate_pitch(clip, rate)
        similarities = [_cosine(signature, item) for item in prototypes]
        best = int(np.argmax(similarities)) if similarities else -1
        duration = max(0.0, float(segment["end"]) - float(segment["start"]))
        threshold = 0.78 if duration >= 0.8 else 0.68
        if best < 0 or (similarities[best] < threshold and len(prototypes) < max_speakers):
            speaker_id = len(prototypes)
            prototypes.append(signature)
            members.append([(signature, pitch)])
        else:
            speaker_id = best
            members[speaker_id].append((signature, pitch))
            prototypes[speaker_id] = np.mean(
                [item[0] for item in members[speaker_id]], axis=0
            )
        assigned.append({**segment, "speaker_id": speaker_id})

    profiles: dict[int, VoiceProfile] = {}
    category_counts = {"male": 0, "female": 0, "child": 0}
    for speaker_id, items in enumerate(members):
        pitches = [pitch for _, pitch in items if pitch > 0]
        pitch = float(np.median(pitches)) if pitches else 190.0
        category = "child" if pitch >= 250 else ("female" if pitch >= 165 else "male")
        order = category_counts[category]
        category_counts[category] += 1
        if category == "male":
            profiles[speaker_id] = VoiceProfile(
                speaker_id, "vi-VN-NamMinhNeural", 0, (-6, 0, 5)[order % 3]
            )
        elif category == "child":
            profiles[speaker_id] = VoiceProfile(
                speaker_id, "vi-VN-HoaiMyNeural", 8, (30, 36, 24)[order % 3]
            )
        else:
            profiles[speaker_id] = VoiceProfile(
                speaker_id, "vi-VN-HoaiMyNeural", 0, (-4, 0, 5)[order % 3]
            )
    return assigned, profiles


def emotion_rate(text: str) -> int:
    """Chỉ thay đổi nhịp nhẹ theo cảm xúc, không đổi loại giọng."""
    value = text.strip()
    if "!" in value:
        return 5
    if "…" in value or "..." in value:
        return -4
    if "?" in value:
        return 1
    return 0
