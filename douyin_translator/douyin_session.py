from __future__ import annotations

import json
import os
import shutil
import socket
import subprocess
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from urllib.request import urlopen

from .errors import AppError
from .system import app_data_dir


@dataclass(frozen=True)
class DouyinSession:
    cookie_file: Path
    user_agent: str


def find_browser() -> Path | None:
    """Tìm Chrome/Edge nhưng tuyệt đối không đọc hồ sơ người dùng của chúng."""
    names = ("chrome.exe", "msedge.exe") if os.name == "nt" else (
        "google-chrome", "chromium", "chromium-browser", "microsoft-edge"
    )
    for name in names:
        found = shutil.which(name)
        if found:
            return Path(found)

    if os.name != "nt":
        return None
    roots = [
        os.getenv("PROGRAMFILES"),
        os.getenv("PROGRAMFILES(X86)"),
        os.getenv("LOCALAPPDATA"),
    ]
    suffixes = (
        Path("Google/Chrome/Application/chrome.exe"),
        Path("Microsoft/Edge/Application/msedge.exe"),
    )
    for root in filter(None, roots):
        for suffix in suffixes:
            candidate = Path(root) / suffix
            if candidate.is_file():
                return candidate
    return None


def _free_local_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        server.bind(("127.0.0.1", 0))
        return int(server.getsockname()[1])


def _read_json(url: str, timeout: float = 2.0):
    with urlopen(url, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def _devtools_info(port: int, timeout_seconds: float = 20.0) -> dict:
    deadline = time.monotonic() + timeout_seconds
    last_error: Exception | None = None
    while time.monotonic() < deadline:
        try:
            return _read_json(f"http://127.0.0.1:{port}/json/version")
        except Exception as exc:
            last_error = exc
            time.sleep(0.25)
    raise RuntimeError(f"Không kết nối được phiên trình duyệt riêng: {last_error}")


def _page_websocket(port: int) -> str:
    targets = _read_json(f"http://127.0.0.1:{port}/json/list")
    for target in targets:
        if target.get("type") == "page" and target.get("webSocketDebuggerUrl"):
            return str(target["webSocketDebuggerUrl"])
    raise RuntimeError("Không tìm thấy trang Douyin trong phiên trình duyệt riêng")


def _cdp_command(websocket_url: str, method: str) -> dict:
    from websockets.sync.client import connect

    # Chrome 111+ kiểm tra Origin của kết nối DevTools. Origin này khớp chính
    # xác với cổng localhost đã truyền qua --remote-allow-origins.
    from urllib.parse import urlparse

    parsed = urlparse(websocket_url)
    origin = f"http://127.0.0.1:{parsed.port}"
    with connect(
        websocket_url,
        origin=origin,
        open_timeout=5,
        close_timeout=2,
    ) as connection:
        request_id = 1
        connection.send(json.dumps({"id": request_id, "method": method}))
        deadline = time.monotonic() + 8
        while time.monotonic() < deadline:
            message = json.loads(connection.recv(timeout=2))
            if message.get("id") == request_id:
                if "error" in message:
                    raise RuntimeError(str(message["error"]))
                return dict(message.get("result") or {})
    raise RuntimeError(f"Trình duyệt không trả lời lệnh {method}")


def _write_netscape_cookies(cookies: list[dict], output: Path) -> Path:
    lines = ["# Netscape HTTP Cookie File", "# Tạo bởi Douyin AI Translator"]
    for cookie in cookies:
        name = str(cookie.get("name") or "")
        value = str(cookie.get("value") or "")
        domain = str(cookie.get("domain") or "")
        if not name or not domain:
            continue
        path = str(cookie.get("path") or "/")
        include_subdomains = "TRUE" if domain.startswith(".") else "FALSE"
        secure = "TRUE" if cookie.get("secure") else "FALSE"
        expires = max(0, int(float(cookie.get("expires") or 0)))
        lines.append("\t".join((domain, include_subdomains, path, secure, str(expires), name, value)))
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return output


def create_douyin_session(target_url: str, progress=lambda percent, message: None) -> DouyinSession:
    browser = find_browser()
    if browser is None:
        raise AppError("DL004", "Không tìm thấy Google Chrome hoặc Microsoft Edge")

    session_root = Path(tempfile.mkdtemp(prefix="douyin_browser_", dir=app_data_dir()))
    cookie_file = app_data_dir() / "douyin_session_cookies.txt"
    port = _free_local_port()
    command = [
        str(browser),
        f"--remote-debugging-port={port}",
        "--remote-debugging-address=127.0.0.1",
        f"--remote-allow-origins=http://127.0.0.1:{port}",
        f"--user-data-dir={session_root}",
        "--no-first-run",
        "--no-default-browser-check",
        "--disable-background-mode",
        "--disable-sync",
        target_url,
    ]
    if os.getenv("DOUYIN_BROWSER_HEADLESS") == "1":
        command.insert(-1, "--headless=new")
        command.insert(-1, "--disable-gpu")
    creationflags = subprocess.CREATE_NEW_PROCESS_GROUP if os.name == "nt" else 0
    process = subprocess.Popen(
        command,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=creationflags,
    )
    try:
        progress(10, "Đã mở Chrome riêng: không đăng nhập, không tắt; ứng dụng sẽ tự đóng...")
        info = _devtools_info(port)
        user_agent = str(info.get("User-Agent") or info.get("userAgent") or "")
        deadline = time.monotonic() + 120
        last_names: set[str] = set()
        ready_since: float | None = None
        while time.monotonic() < deadline:
            try:
                # Trên Windows, chrome.exe có thể bàn giao cửa sổ cho tiến trình
                # con rồi tiến trình Popen ban đầu kết thúc ngay. Vì vậy không
                # dùng process.poll() để kết luận cửa sổ đã đóng; phiên còn sống
                # hay không phải được xác định bằng cổng DevTools riêng.
                _devtools_info(port, timeout_seconds=1.0)
                result = _cdp_command(_page_websocket(port), "Network.getAllCookies")
                cookies = list(result.get("cookies") or [])
                douyin_cookies = [
                    cookie for cookie in cookies
                    if "douyin.com" in str(cookie.get("domain") or "")
                ]
                last_names = {str(cookie.get("name") or "") for cookie in douyin_cookies}
                if douyin_cookies and ({"s_v_web_id", "ttwid"} & last_names):
                    # Cookie cơ bản thường xuất hiện trước khi Douyin hoàn tất
                    # JavaScript chống bot. Chờ ổn định vài giây để tránh đóng
                    # trình duyệt quá sớm rồi nhận lỗi "Fresh cookies".
                    ready_since = ready_since or time.monotonic()
                    if time.monotonic() - ready_since >= 5:
                        _write_netscape_cookies(douyin_cookies, cookie_file)
                        return DouyinSession(cookie_file=cookie_file, user_agent=user_agent)
                else:
                    ready_since = None
            except Exception:
                pass
            progress(12, "Giữ nguyên cửa sổ Chrome riêng; không cần đăng nhập, ứng dụng sẽ tự đóng...")
            time.sleep(2)
        raise AppError("DL004", "Không nhận được cookie Douyin sau 120 giây; cookie thấy được: " + ", ".join(sorted(last_names)))
    except AppError:
        raise
    except Exception as exc:
        raise AppError("DL004", str(exc)) from exc
    finally:
        # Luôn đóng đúng phiên qua DevTools. Kể cả launcher process đã thoát,
        # tiến trình Chrome con và cửa sổ riêng vẫn có thể đang hoạt động.
        try:
            _cdp_command(_page_websocket(port), "Browser.close")
        except Exception:
            pass
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
        shutil.rmtree(session_root, ignore_errors=True)
