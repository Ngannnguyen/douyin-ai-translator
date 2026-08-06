from __future__ import annotations

import time

from .errors import AppError


def translate_segments(segments: list[dict], progress) -> list[dict]:
    try:
        from deep_translator import GoogleTranslator

        translator = GoogleTranslator(source="zh-CN", target="vi")
        total = len(segments)
        output = []
        for index, segment in enumerate(segments, start=1):
            translated = None
            last_error = None
            for attempt in range(3):
                try:
                    translated = translator.translate(segment["text"])
                    break
                except Exception as exc:
                    last_error = exc
                    time.sleep(1.5 * (attempt + 1))
            if not translated:
                raise RuntimeError(f"Đoạn {index}: {last_error}")
            output.append({**segment, "text": translated.strip()})
            progress(52 + int(23 * index / total), f"Đang dịch tiếng Việt: {index}/{total} đoạn")
        return output
    except Exception as exc:
        raise AppError("TR001", str(exc)) from exc
