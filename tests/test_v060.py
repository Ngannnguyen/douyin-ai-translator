from __future__ import annotations

import sys
import wave
from pathlib import Path

import numpy as np

import douyin_translator.media as media
from douyin_translator import separation
from douyin_translator.speaker import assign_speakers
from douyin_translator.subtitle_removal import detect_subtitle_mask, remove_subtitles_from_frame
from douyin_translator.translation import fit_text_to_duration
from douyin_translator.voice import tempo_filters


def test_no_blur_bar_or_black_bar(tmp_path: Path):
    subtitle = tmp_path / "vi.srt"
    subtitle.write_text("", encoding="utf-8")
    value = media.subtitle_video_filter(subtitle, hide_original=True)
    assert "boxblur" not in value
    assert "drawbox" not in value
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


def test_long_translation_is_shortened_before_tts():
    long_text = (
        "Có thể nói rằng sản phẩm này thực sự rất tiện lợi và giúp chúng ta "
        "tiết kiệm rất nhiều thời gian trong cuộc sống hàng ngày"
    )
    result = fit_text_to_duration(long_text, 2.0)
    assert len(result.split()) <= 7
    assert "tiết kiệm thời gian" in result.lower()
    assert result.endswith(".")


def test_tts_speed_never_becomes_machine_like():
    for source, target in [(8, 1), (1, 8), (2.1, 2.0)]:
        value = float(tempo_filters(source, target).split("=")[1])
        assert 0.92 <= value <= 1.12


def test_windowed_exe_demucs_download_has_writable_streams(monkeypatch):
    old_count = len(separation._AI_SINKS)
    monkeypatch.setattr(sys, "stdout", None)
    monkeypatch.setattr(sys, "stderr", None)
    separation.ensure_writable_standard_streams()
    assert callable(sys.stdout.write)
    assert callable(sys.stderr.write)
    for sink in separation._AI_SINKS[old_count:]:
        assert not sink.closed
