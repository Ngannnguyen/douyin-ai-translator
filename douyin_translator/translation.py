from __future__ import annotations

import re
import time

from .errors import AppError


_COMPACT_REPLACEMENTS = (
    (r"\bcó thể nói rằng\b", ""),
    (r"\bchúng ta có thể thấy rằng\b", ""),
    (r"\bnhư mọi người có thể thấy\b", ""),
    (r"\bthực sự rất\b", "rất"),
    (r"\brất rất\b", "rất"),
    (r"\brất nhiều\b", "nhiều"),
    (r"\btrong cuộc sống hàng ngày\b", "mỗi ngày"),
    (r"\bmột cách nhanh chóng\b", "nhanh"),
    (r"\bmột cách dễ dàng\b", "dễ dàng"),
    (r"\bở thời điểm hiện tại\b", "hiện tại"),
    (r"\bđiều mà\b", "điều"),
)
_LOW_VALUE_WORDS = {
    "thực", "sự", "rất", "thì", "mà", "cũng", "đã", "đang", "sẽ",
    "những", "các", "một", "này", "đó", "nói", "chung", "kiểu", "nhé",
}
_IMPORTANT_WORDS = {
    "không", "đừng", "phải", "cần", "giúp", "tiết", "kiệm", "nguy",
    "hiểm", "nhanh", "dễ", "mẹo", "lưu", "ý", "vì", "nên",
}


def _clean_text(text: str) -> str:
    value = re.sub(r"\s+", " ", str(text)).strip()
    for pattern, replacement in _COMPACT_REPLACEMENTS:
        value = re.sub(pattern, replacement, value, flags=re.IGNORECASE)
    value = re.sub(r"\s+([,.!?;:])", r"\1", value)
    value = re.sub(r"\s{2,}", " ", value).strip(" ,;:")
    return value


def shorten_text(text: str, max_words: int) -> str:
    """Rút gọn theo cụm ý, không cắt ký tự hoặc ép giọng đọc quá nhanh."""
    # Câu thoại rất ngắn (khoảng 1–2 giây) đôi khi chỉ đủ chỗ cho một
    # hoặc hai từ. Không ép tối thiểu ba từ vì TTS sẽ phải đọc quá nhanh
    # hoặc bị cắt mất phần cuối.
    max_words = max(1, int(max_words))
    value = _clean_text(text)
    words = value.split()
    if len(words) <= max_words:
        return value

    # Các cấu trúc bán hàng phổ biến được viết lại theo ý tương đương hoàn
    # chỉnh, không nhặt từng từ rời rạc.
    lowered = value.lower()
    if "tiết kiệm" in lowered and "thời gian" in lowered:
        if max_words >= 6 and "sản phẩm" in lowered:
            return "Sản phẩm giúp tiết kiệm thời gian."
        if max_words >= 4:
            return "Giúp tiết kiệm thời gian."
        return "Giúp tiết kiệm."
    if "cần lưu ý" in lowered or "hãy lưu ý" in lowered:
        tail = re.split(r"(?:cần|hãy) lưu ý", value, maxsplit=1, flags=re.IGNORECASE)[-1]
        compact = ("Lưu ý " + tail.strip(" ,:")).strip()
        compact_words = compact.split()
        if len(compact_words) <= max_words:
            return compact.rstrip(".") + "."
    if "không nên" in lowered:
        tail = re.split(r"không nên", value, maxsplit=1, flags=re.IGNORECASE)[-1]
        compact = ("Không nên " + tail.strip(" ,:")).strip()
        if len(compact.split()) <= max_words:
            return compact.rstrip(".") + "."

    clauses = [
        item.strip(" ,;:")
        for item in re.split(r"[.!?;]+|\s+(?:nhưng|tuy nhiên|bởi vì|cho nên|và sau đó)\s+", value)
        if item.strip(" ,;:")
    ]
    if len(clauses) > 1:
        scored = []
        for index, clause in enumerate(clauses):
            clause_words = clause.lower().split()
            score = sum(word in _IMPORTANT_WORDS for word in clause_words) * 3
            score += sum(char.isdigit() for char in clause)
            score += 1 if index == 0 else 0
            score -= max(0, len(clause_words) - max_words) * 0.1
            scored.append((score, index, clause))
        chosen = []
        used = 0
        for _, index, clause in sorted(scored, key=lambda item: (-item[0], item[1])):
            size = len(clause.split())
            if used + size <= max_words or not chosen:
                chosen.append((index, clause))
                used += size
        value = ", ".join(clause for _, clause in sorted(chosen))
        words = value.split()
        if len(words) <= max_words:
            return value.rstrip(" ,;:") + ("?" if "?" in text else ".")

    # Bỏ từ đệm trước, giữ từ phủ định, hành động, con số và ý chính.
    # Ghép cụm nghĩa trước khi lọc để “tiết kiệm”, “thời gian” hoặc
    # “không nên” không bao giờ bị tách thành từ đơn vô nghĩa.
    protected = value
    protected_phrases = {
        "tiết kiệm": "tiết_kiệm",
        "thời gian": "thời_gian",
        "sản phẩm": "sản_phẩm",
        "không nên": "không_nên",
        "cần phải": "cần_phải",
        "lưu ý": "lưu_ý",
    }
    for phrase, token in protected_phrases.items():
        protected = re.sub(phrase, token, protected, flags=re.IGNORECASE)
    words = protected.split()
    kept = [word for word in words if word.lower().strip(".,!?") not in _LOW_VALUE_WORDS]
    if len(kept) < min(3, max_words):
        kept = words
    if len(kept) > max_words:
        important_indexes = [
            index for index, word in enumerate(kept)
            if word.lower().strip(".,!?") in _IMPORTANT_WORDS or any(c.isdigit() for c in word)
        ]
        selected = set(range(min(max_words, len(kept))))
        for index in important_indexes:
            if index not in selected and len(selected) >= max_words:
                selected.remove(max(selected))
            selected.add(index)
        kept = [word for index, word in enumerate(kept) if index in selected][:max_words]
    result = " ".join(kept).replace("_", " ").strip(" ,;:.")
    return result + ("?" if "?" in text else ".")


def fit_text_to_duration(text: str, duration: float) -> str:
    # Tiếng Việt tự nhiên khoảng 3–3.5 âm tiết/từ mỗi giây.
    budget = max(1, round(max(0.25, duration) * 3.2))
    return shorten_text(text, budget)


def translate_segments(segments: list[dict], progress) -> list[dict]:
    try:
        from deep_translator import GoogleTranslator

        if not segments:
            raise RuntimeError("Không có đoạn tiếng Trung để dịch")
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
            translated_text = str(translated or "").strip()
            if not translated_text:
                raise RuntimeError(f"Đoạn {index}: {last_error}")
            duration = max(0.25, float(segment["end"]) - float(segment["start"]))
            natural_text = fit_text_to_duration(translated_text, duration)
            output.append({
                **segment,
                "text": natural_text,
                "translation_full": translated_text,
            })
            progress(
                52 + int(23 * index / total),
                f"Đang dịch tự nhiên theo thời lượng: {index}/{total} đoạn",
            )
        return output
    except Exception as exc:
        raise AppError("TR001", str(exc)) from exc
