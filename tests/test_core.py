from pathlib import Path
from types import SimpleNamespace

import numpy as np

import douyin_translator.downloader as downloader
import douyin_translator.media as media
from douyin_translator.errors import AppError
from douyin_translator.subtitles import srt_time, write_srt
from douyin_translator.diagnostics import CheckItem, DiagnosticReport
from douyin_translator.downloader import download_options, extract_url, normalize_douyin_url
from douyin_translator.douyin_session import _write_netscape_cookies
from douyin_translator.pipeline import unique_path
from douyin_translator import separation
from douyin_translator.voice import CHILD_VOICE, FEMALE_VOICE, MALE_VOICE, choose_voice, tempo_filters


def test_srt_time():
    assert srt_time(0) == "00:00:00,000"
    assert srt_time(3661.234) == "01:01:01,234"


def test_write_srt(tmp_path: Path):
    output = write_srt([{"start": 0.1, "end": 1.8, "text": "Xin chào"}], tmp_path / "test.srt")
    content = output.read_text(encoding="utf-8-sig")
    assert "00:00:00,100 --> 00:00:01,800" in content
    assert "Xin chào" in content


def test_srt_contains_real_timeline_and_text(tmp_path: Path):
    output = write_srt(
        [{"start": 2.0, "end": 4.2, "text": "Nội dung phụ đề thực"}],
        tmp_path / "verified.srt",
    )
    content = output.read_text(encoding="utf-8-sig")
    assert " --> " in content
    assert len(content.strip()) >= 20


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


def test_extract_url_from_real_douyin_share_text():
    shared = (
        "7.64 :7pm w@s.eo 09/24 vSl:/ 坚持中华传统美德的传承 "
        "# 轻漫计划 # 原创动画 https://v.douyin.com/D8234TU1NNk/ "
        "复制此链接，打开Dou音搜索，直接观看视频！"
    )
    assert extract_url(shared) == "https://v.douyin.com/D8234TU1NNk/"


def test_extract_url_from_markdown_share_text():
    shared = (
        "Xem video [https://v.douyin.com/D8234TU1NNk/]"
        "(https://v.douyin.com/D8234TU1NNk/) rồi mở Douyin"
    )
    assert extract_url(shared) == "https://v.douyin.com/D8234TU1NNk/"


def test_safe_mode_never_reads_browser_cookies():
    options = download_options(
        "https://www.douyin.com/video/7552467869231254847",
        "video_goc.%(ext)s",
    )
    assert "cookiesfrombrowser" not in options
    assert "cookiefile" not in options


def test_other_sites_do_not_read_browser_cookies():
    options = download_options("https://example.com/video", "video_goc.%(ext)s")
    assert "cookiesfrombrowser" not in options


def test_cookie_error_is_in_vietnamese():
    message = AppError("DL003", "Fresh cookies are needed").user_message
    assert "phiên truy cập mới" in message
    assert "không đọc dữ liệu Chrome/Edge cá nhân" in message


def test_session_cookie_file_is_netscape_compatible(tmp_path: Path):
    output = _write_netscape_cookies(
        [{
            "domain": ".douyin.com",
            "path": "/",
            "secure": True,
            "expires": 1999999999.0,
            "name": "ttwid",
            "value": "safe-session-value",
        }],
        tmp_path / "cookies.txt",
    )
    content = output.read_text(encoding="utf-8")
    assert content.startswith("# Netscape HTTP Cookie File")
    assert ".douyin.com\tTRUE\t/\tTRUE\t1999999999\tttwid\tsafe-session-value" in content


def test_download_options_accept_only_explicit_session_cookie(tmp_path: Path):
    cookie_file = tmp_path / "cookies.txt"
    options = download_options(
        "https://www.douyin.com/video/7644014700174331190",
        "video_goc.%(ext)s",
        cookie_file=cookie_file,
        user_agent="Test Browser",
    )
    assert options["cookiefile"] == str(cookie_file)
    assert options["http_headers"]["User-Agent"] == "Test Browser"


def test_douyin_failure_retries_with_isolated_session(tmp_path: Path, monkeypatch):
    cookie_file = tmp_path / "session.txt"
    cookie_file.write_text("# Netscape HTTP Cookie File\n", encoding="utf-8")
    expected = tmp_path / "video_goc.mp4"
    attempts = []

    def fake_download(source, work_dir, cookie_file=None, user_agent=""):
        attempts.append((source, cookie_file, user_agent))
        if len(attempts) == 1:
            raise RuntimeError("HTTP Error 403")
        expected.write_bytes(b"video")
        return expected

    monkeypatch.setattr(downloader, "_download", fake_download)
    import douyin_translator.douyin_session as session_module
    monkeypatch.setattr(
        session_module,
        "create_douyin_session",
        lambda source, progress: SimpleNamespace(
            cookie_file=cookie_file,
            user_agent="Isolated Browser",
        ),
    )

    result = downloader.obtain_video(
        "https://v.douyin.com/D8234TU1NNk/",
        tmp_path,
        lambda percent, message: None,
    )
    assert result == expected
    assert attempts[0][1] is None
    assert attempts[1][1] == cookie_file
    assert attempts[1][2] == "Isolated Browser"


def test_session_survives_when_windows_launcher_exits(tmp_path: Path, monkeypatch):
    import douyin_translator.douyin_session as session_module

    class DetachedLauncher:
        def poll(self):
            return 0

    commands = []
    monkeypatch.setattr(session_module, "find_browser", lambda: Path("chrome.exe"))
    monkeypatch.setattr(session_module, "app_data_dir", lambda: tmp_path)
    monkeypatch.setattr(session_module, "_free_local_port", lambda: 9229)
    monkeypatch.setattr(
        session_module.subprocess,
        "Popen",
        lambda *args, **kwargs: DetachedLauncher(),
    )
    monkeypatch.setattr(
        session_module,
        "_devtools_info",
        lambda port, timeout_seconds=20.0: {"User-Agent": "Windows Chrome"},
    )
    monkeypatch.setattr(session_module, "_page_websocket", lambda port: "ws://127.0.0.1:9229/page")

    def fake_cdp(url, method):
        commands.append(method)
        if method == "Network.getAllCookies":
            return {
                "cookies": [{
                    "domain": ".douyin.com",
                    "path": "/",
                    "secure": True,
                    "expires": 1999999999,
                    "name": "ttwid",
                    "value": "detached-launcher-session",
                }]
            }
        return {}

    monkeypatch.setattr(session_module, "_cdp_command", fake_cdp)
    session = session_module.create_douyin_session(
        "https://v.douyin.com/example/",
        lambda percent, message: None,
    )

    assert session.user_agent == "Windows Chrome"
    assert session.cookie_file.is_file()
    assert "Network.getAllCookies" in commands
    assert "Browser.close" in commands


def test_unique_path_does_not_overwrite(tmp_path: Path):
    existing = tmp_path / "ket_qua.mp4"
    existing.write_bytes(b"old")
    assert unique_path(existing).name == "ket_qua_2.mp4"


def test_auto_voice_uses_original_pitch():
    rate = 16000
    seconds = np.arange(rate, dtype=np.float32) / rate
    male = np.sin(2 * np.pi * 120 * seconds).astype(np.float32)
    female = np.sin(2 * np.pi * 220 * seconds).astype(np.float32)
    child = np.sin(2 * np.pi * 290 * seconds).astype(np.float32)
    assert choose_voice(male, rate) == MALE_VOICE
    assert choose_voice(female, rate) == FEMALE_VOICE
    assert choose_voice(child, rate) == CHILD_VOICE


def test_voice_tempo_filter_stays_in_ffmpeg_range():
    values = [float(item.split("=")[1]) for item in tempo_filters(8.0, 1.0).split(",")]
    assert all(0.5 <= value <= 2.0 for value in values)


def test_subtitle_filter_blurs_chinese_caption_area(tmp_path: Path):
    subtitle = tmp_path / "phu de vi.srt"
    subtitle.write_text("", encoding="utf-8")
    video_filter = media.subtitle_video_filter(subtitle, hide_original=True)
    assert "crop=iw:ih*0.30" in video_filter
    assert "boxblur=20:3" in video_filter
    assert "drawbox=" in video_filter
    assert "subtitles=" in video_filter


def test_dual_audio_keeps_original_and_adds_vietnamese(tmp_path: Path, monkeypatch):
    commands = []
    monkeypatch.setattr(media, "get_ffmpeg", lambda: "ffmpeg")
    monkeypatch.setattr(media, "_run", lambda command, code: commands.append(command))
    media.burn_subtitles(
        tmp_path / "video.mp4",
        tmp_path / "sub.srt",
        tmp_path / "out.mp4",
        hide_original=True,
        voice_audio=tmp_path / "voice.wav",
    )
    command = commands[0]
    graph = command[command.index("-filter_complex") + 1]
    assert "[0:a]volume=0.35[bg]" in graph
    assert "[1:a]volume=1.15[voice]" in graph


def test_replace_audio_uses_separated_background(tmp_path: Path, monkeypatch):
    commands = []
    monkeypatch.setattr(media, "get_ffmpeg", lambda: "ffmpeg")
    monkeypatch.setattr(media, "_run", lambda command, code: commands.append(command))
    media.burn_subtitles(
        tmp_path / "video.mp4",
        tmp_path / "sub.srt",
        tmp_path / "out.mp4",
        hide_original=True,
        voice_audio=tmp_path / "voice.wav",
        background_audio=tmp_path / "background.wav",
    )
    command = commands[0]
    graph = command[command.index("-filter_complex") + 1]
    assert "[2:a]volume=1.0[bg]" in graph
    assert command.count("-i") == 3


def test_demucs_401_uses_supported_internal_api():
    source = Path(separation.__file__).read_text(encoding="utf-8")
    assert "from demucs.api" not in source
    assert "from demucs.apply import apply_model" in source
    assert "from demucs.pretrained import get_model" in source
