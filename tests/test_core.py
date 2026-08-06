from pathlib import Path

from douyin_translator.errors import AppError
from douyin_translator.subtitles import srt_time, write_srt
from douyin_translator.diagnostics import CheckItem, DiagnosticReport


def test_srt_time():
    assert srt_time(0) == "00:00:00,000"
    assert srt_time(3661.234) == "01:01:01,234"


def test_write_srt(tmp_path: Path):
    output = write_srt([{"start": 0.1, "end": 1.8, "text": "Xin chào"}], tmp_path / "test.srt")
    content = output.read_text(encoding="utf-8-sig")
    assert "00:00:00,100 --> 00:00:01,800" in content
    assert "Xin chào" in content


def test_vietnamese_error_message():
    message = AppError("DL001", "HTTP 403").user_message
    assert "Không tải được video" in message
    assert "Cách xử lý" in message
    assert "HTTP 403" in message


def test_diagnostic_report():
    report = DiagnosticReport([CheckItem("Python", True, "3.11 64-bit")])
    assert report.passed
    assert "Máy đã sẵn sàng" in report.as_text()
