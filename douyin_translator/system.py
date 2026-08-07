from __future__ import annotations

import os
import shutil
import sys
import tempfile
from pathlib import Path

from .errors import AppError


def app_data_dir() -> Path:
    root = Path(os.getenv("LOCALAPPDATA", Path.home())) / "DouyinAITranslator"
    root.mkdir(parents=True, exist_ok=True)
    return root


def get_ffmpeg() -> str:
    try:
        import imageio_ffmpeg

        path = imageio_ffmpeg.get_ffmpeg_exe()
        if not Path(path).exists():
            raise FileNotFoundError(path)
        return path
    except Exception as exc:
        raise AppError("SYS001", str(exc)) from exc


def choose_model() -> str:
    total_gb, available_gb = memory_info_gb()
    return "base" if total_gb >= 16 and available_gb >= 8 else "tiny"


def safe_thread_count() -> int:
    total_gb, available_gb = memory_info_gb()
    return 4 if total_gb >= 24 and available_gb >= 8 else 2


def memory_info_gb() -> tuple[float, float]:
    try:
        import ctypes

        class MemoryStatus(ctypes.Structure):
            _fields_ = [("length", ctypes.c_ulong), ("memory_load", ctypes.c_ulong),
                        ("total_phys", ctypes.c_ulonglong), ("avail_phys", ctypes.c_ulonglong),
                        ("total_page", ctypes.c_ulonglong), ("avail_page", ctypes.c_ulonglong),
                        ("total_virtual", ctypes.c_ulonglong), ("avail_virtual", ctypes.c_ulonglong),
                        ("avail_extended_virtual", ctypes.c_ulonglong)]

        status = MemoryStatus()
        status.length = ctypes.sizeof(MemoryStatus)
        if not ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status)):
            raise OSError("Không đọc được trạng thái bộ nhớ")
        return status.total_phys / (1024 ** 3), status.avail_phys / (1024 ** 3)
    except Exception:
        return 8.0, 4.0


def validate_resources(min_available_gb: float = 2.0) -> None:
    _, available_gb = memory_info_gb()
    if available_gb < min_available_gb:
        raise AppError(
            "SYS005",
            f"RAM khả dụng: {available_gb:.1f} GB; cần tối thiểu {min_available_gb:.1f} GB",
        )


def validate_output_dir(output_dir: Path) -> None:
    try:
        output_dir.mkdir(parents=True, exist_ok=True)
        free_bytes = shutil.disk_usage(output_dir).free
        if free_bytes < 2 * 1024 ** 3:
            raise AppError("SYS002", f"Còn trống {free_bytes / 1024 ** 3:.2f} GB tại {output_dir}")
        with tempfile.NamedTemporaryFile(prefix="kiem_tra_", dir=output_dir, delete=True):
            pass
    except AppError:
        raise
    except Exception as exc:
        raise AppError("SYS003", str(exc)) from exc


def check_python() -> tuple[bool, str]:
    is_64_bit = sys.maxsize > 2 ** 32
    version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    ok = is_64_bit and sys.version_info >= (3, 10)
    detail = f"Python {version}, {'64-bit' if is_64_bit else '32-bit'}"
    return ok, detail


def check_dependencies() -> tuple[bool, str]:
    missing = []
    for package in (
        "faster_whisper", "deep_translator", "yt_dlp", "imageio_ffmpeg",
        "edge_tts", "demucs", "torch", "torchaudio",
    ):
        try:
            __import__(package)
        except ImportError:
            missing.append(package)
    return not missing, "Đầy đủ" if not missing else "Thiếu: " + ", ".join(missing)
