from pathlib import Path

from douyin_translator.errors import AppError
from douyin_translator.subtitles import srt_time, write_srt
from douyin_translator.diagnostics import CheckItem, DiagnosticReport
from douyin_translator.downloader import download_options, extract_url, normalize_douyin_url


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


def test_normalize_douyin_user_modal_url():
    source = (
        "https://www.douyin.com/user/MS4wLjABAAAA-example"
        "?from_tab_name=main&modal_id=7552467869231254847&vid=7497139388212874547"
    )
    assert normalize_douyin_url(source) == "https://www.douyin.com/video/7552467869231254847"


def test_normalize_douyin_vid_fallback():
    source = "https://www.douyin.com/user/example?vid=7497139388212874547"
    assert normalize_douyin_url(source) == "https://www.douyin.com/video/7497139388212874547"


def test_extract_url_from_share_text():
    shared = "5.88 复制打开抖音 https://v.douyin.com/abc123/ 看视频！"
    assert extract_url(shared) == "https://v.douyin.com/abc123/"


def test_douyin_uses_edge_cookies():
    options = download_options(
        "https://www.douyin.com/video/7552467869231254847",
        "video_goc.%(ext)s",
    )
    assert options["cookiesfrombrowser"] == ("edge",)


def test_other_sites_do_not_read_browser_cookies():
    options = download_options("https://example.com/video", "video_goc.%(ext)s")
    assert "cookiesfrombrowser" not in options


def test_cookie_error_is_in_vietnamese():
    message = AppError("DL002", "Fresh cookies are needed").user_message
    assert "Microsoft Edge" in message
    assert "đóng hoàn toàn Edge" in message
