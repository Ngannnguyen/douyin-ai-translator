from __future__ import annotations

import sys
import wave
from pathlib import Path

import numpy as np
import pytest

import douyin_translator.media as media
import douyin_translator.voice as voice_module
from douyin_translator import separation
from douyin_translator.speaker import assign_speakers
from douyin_translator.subtitle_removal import detect_subtitle_mask, remove_subtitles_from_frame
from douyin_translator.translation import merge_source_segments
from douyin_translator.voice import tempo_filters


def test_caption_panel_hides_chinese_subtitle_area(tmp_path: Path):
    subtitle = tmp_path / "vi.srt"
    subtitle.write_text("", encoding="utf-8")
    value = media.subtitle_video_filter(subtitle, hide_original=True)
    assert "boxblur" not in value
    assert "drawbox" in value
    assert "black@1.0" in value
    assert "crop=" not in value
    assert "subtitles=" in value


def test_remove_only_text_pixels_not_whole_bottom_strip():
    import cv2

    frame = np.full((360, 640, 3), 70, dtype=np.uint8)
    cv2.putText(
        frame, "Chinese subtitle", (150, 310),
        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2, cv2.LINE_AA,
    )
    mask = detect_subtitle_mask(frame)
    assert np.count_nonzero(mask) > 50
    assert np.count_nonzero(mask) < frame.shape[0] * frame.shape[1] * 0.08
    cleaned, used_mask = remove_subtitles_from_frame(frame)
    assert np.array_equal(mask, used_mask)
    assert not np.array_equal(frame, cleaned)


def test_same_speaker_keeps_same_id_and_voice_profile(tmp_path: Path):
    rate = 16000
    one = np.arange(rate, dtype=np.float32) / rate
    male = (np.sin(2 * np.pi * 120 * one) * 12000).astype("<i2")
    female = (np.sin(2 * np.pi * 220 * one) * 12000).astype("<i2")
    pcm = np.concatenate([male, female, male, female])
    audio = tmp_path / "voices.wav"
    with wave.open(str(audio), "wb") as target:
        target.setnchannels(1)
        target.setsampwidth(2)
        target.setframerate(rate)
        target.writeframes(pcm.tobytes())
    segments = [
        {"start": 0, "end": 1, "text": "a"},
        {"start": 1, "end": 2, "text": "b"},
        {"start": 2, "end": 3, "text": "c"},
        {"start": 3, "end": 4, "text": "d"},
    ]
    assigned, profiles = assign_speakers(segments, audio)
    assert assigned[0]["speaker_id"] == assigned[2]["speaker_id"]
    assert assigned[1]["speaker_id"] == assigned[3]["speaker_id"]
    assert profiles[assigned[0]["speaker_id"]].voice == "vi-VN-NamMinhNeural"
    assert profiles[assigned[1]["speaker_id"]].voice == "vi-VN-HoaiMyNeural"


def test_short_whisper_fragments_are_merged_before_translation():
    result = merge_source_segments([
        {"start": 0.0, "end": 0.8, "text": "这是"},
        {"start": 0.9, "end": 1.8, "text": "一个完整"},
        {"start": 1.9, "end": 2.8, "text": "句子。"},
    ])
    assert len(result) == 1
    assert result[0]["text"] == "这是一个完整句子。"


def test_narrator_keeps_full_meaning_and_extends_timeline(tmp_path: Path, monkeypatch):
    rate = 16000
    timeline = np.arange(rate * 2, dtype=np.float32) / rate
    pcm = (np.sin(2 * np.pi * 120 * timeline) * 12000).astype("<i2")
    source = tmp_path / "source.wav"
    with wave.open(str(source), "wb") as target:
        target.setnchannels(1)
        target.setsampwidth(2)
        target.setframerate(rate)
        target.writeframes(pcm.tobytes())

    spoken = {"text": "", "profile": None}

    async def fake_save(text, profile, output, rate_delta=0):
        spoken["text"] = text
        spoken["profile"] = profile
        output.write_bytes(b"mock")

    def fake_decode(mp3, output):
        seconds = 2.4
        samples = np.zeros(round(24000 * seconds), dtype="<i2")
        with wave.open(str(output), "wb") as target:
            target.setnchannels(1)
            target.setsampwidth(2)
            target.setframerate(24000)
            target.writeframes(samples.tobytes())
        return output

    monkeypatch.setattr(voice_module, "_save_tts", fake_save)
    monkeypatch.setattr(voice_module, "_decode_mp3", fake_decode)
    monkeypatch.setattr(voice_module, "_fit_decoded_clip", lambda decoded, output, seconds: decoded)
    def fake_mix(clips, duration, output):
        output.write_bytes(b"ok")
        return output

    monkeypatch.setattr(voice_module, "_mix_wav_clips", fake_mix)
    segments = [{"start": 0.0, "end": 1.0, "text": "Xin chào, đây là giọng Việt."}]
    result = voice_module.create_vietnamese_voice(
        segments, source, tmp_path / "voice.wav", tmp_path
    )
    assert result.is_file()
    assert segments[0]["text"] == "Xin chào, đây là giọng Việt."
    assert segments[0]["end"] >= 2.4
    assert spoken["profile"].voice == "vi-VN-HoaiMyNeural"
    assert spoken["profile"].rate_percent == 8


def test_all_segments_use_one_cheerful_narrator(tmp_path: Path, monkeypatch):
    rate = 16000
    source = tmp_path / "source.wav"
    with wave.open(str(source), "wb") as target:
        target.setnchannels(1)
        target.setsampwidth(2)
        target.setframerate(rate)
        target.writeframes(np.zeros(rate * 2, dtype="<i2").tobytes())

    async def fake_save(text, profile, output, rate_delta=0):
        output.write_bytes(b"mock")

    profiles = []
    async def fake_save_with_profile(text, profile, output, rate_delta=0):
        profiles.append(profile)
        output.write_bytes(b"mock")

    def fake_decode(mp3, output):
        samples = np.zeros(round(24000 * 0.8), dtype="<i2")
        with wave.open(str(output), "wb") as target:
            target.setnchannels(1)
            target.setsampwidth(2)
            target.setframerate(24000)
            target.writeframes(samples.tobytes())
        return output

    def fake_fit(decoded, output, seconds):
        samples = np.zeros(round(24000 * seconds), dtype="<i2")
        with wave.open(str(output), "wb") as target:
            target.setnchannels(1)
            target.setsampwidth(2)
            target.setframerate(24000)
            target.writeframes(samples.tobytes())
        return output

    monkeypatch.setattr(voice_module, "_save_tts", fake_save_with_profile)
    monkeypatch.setattr(voice_module, "_decode_mp3", fake_decode)
    monkeypatch.setattr(voice_module, "_fit_decoded_clip", fake_fit)
    def fake_mix(clips, duration, output):
        output.write_bytes(b"ok")
        return output

    monkeypatch.setattr(voice_module, "_mix_wav_clips", fake_mix)
    segments = [
        {"start": 0.0, "end": 1.0, "text": "Câu thứ nhất đầy đủ."},
        {"start": 1.1, "end": 2.0, "text": "Câu thứ hai đầy đủ."},
    ]
    result = voice_module.create_vietnamese_voice(
        segments, source, tmp_path / "voice.wav", tmp_path
    )
    assert result.is_file()
    assert len(profiles) == 2
    assert {item.voice for item in profiles} == {"vi-VN-HoaiMyNeural"}
    assert {item.rate_percent for item in profiles} == {8}
    assert {item.pitch_hz for item in profiles} == {8}


def test_tts_speed_never_becomes_machine_like():
    for source, target in [(8, 1), (1, 8), (2.1, 2.0)]:
        value = float(tempo_filters(source, target).split("=")[1])
        assert 0.92 <= value <= 1.20


def test_timeline_validation_rejects_overflowing_voice(tmp_path: Path):
    path = tmp_path / "voice.wav"
    samples = np.zeros(24000 * 2, dtype="<i2")
    with wave.open(str(path), "wb") as target:
        target.setnchannels(1)
        target.setsampwidth(2)
        target.setframerate(24000)
        target.writeframes(samples.tobytes())
    with pytest.raises(ValueError, match="vượt timeline"):
        voice_module._validate_timeline_clip(path, 1.0, 3)


def test_windowed_exe_demucs_download_has_writable_streams(monkeypatch):
    old_count = len(separation._AI_SINKS)
    monkeypatch.setattr(sys, "stdout", None)
    monkeypatch.setattr(sys, "stderr", None)
    separation.ensure_writable_standard_streams()
    assert callable(sys.stdout.write)
    assert callable(sys.stderr.write)
    for sink in separation._AI_SINKS[old_count:]:
        assert not sink.closed
