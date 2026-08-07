from __future__ import annotations

import platform
import shutil
from dataclasses import dataclass
from pathlib import Path

from .system import check_dependencies, check_python, get_ffmpeg, memory_info_gb, validate_output_dir


@dataclass
class CheckItem:
    name: str
    passed: bool
    detail: str


@dataclass
class DiagnosticReport:
    items: list[CheckItem]

    @property
    def passed(self) -> bool:
        return all(item.passed for item in self.items)

    def as_text(self) -> str:
        lines = ["KẾT QUẢ KIỂM TRA MÁY", ""]
        for item in self.items:
            lines.append(f"{'✓' if item.passed else '✗'} {item.name}: {item.detail}")
        lines.extend(["", "Kết luận: " + ("Máy đã sẵn sàng." if self.passed else "Máy chưa sẵn sàng. Hãy sửa các mục có dấu ✗.")])
        return "\n".join(lines)


def run_diagnostics(output_dir: Path) -> DiagnosticReport:
    items: list[CheckItem] = []
    windows_ok = platform.system() == "Windows"
    items.append(CheckItem("Hệ điều hành", windows_ok, f"{platform.system()} {platform.release()}"))

    python_ok, python_detail = check_python()
    items.append(CheckItem("Python", python_ok, python_detail))

    deps_ok, deps_detail = check_dependencies()
    items.append(CheckItem("Thư viện ứng dụng", deps_ok, deps_detail))

    total_gb, available_gb = memory_info_gb()
    items.append(CheckItem("Bộ nhớ RAM", available_gb >= 2, f"Tổng {total_gb:.1f} GB, khả dụng {available_gb:.1f} GB"))

    try:
        ffmpeg_path = get_ffmpeg()
        items.append(CheckItem("Bộ xử lý video FFmpeg", True, str(ffmpeg_path)))
    except Exception as exc:
        items.append(CheckItem("Bộ xử lý video FFmpeg", False, str(exc)))

    try:
        validate_output_dir(output_dir)
        free_gb = shutil.disk_usage(output_dir).free / 1024 ** 3
        items.append(CheckItem("Thư mục kết quả", True, f"Có thể ghi, còn trống {free_gb:.1f} GB"))
    except Exception as exc:
        items.append(CheckItem("Thư mục kết quả", False, str(exc)))

    return DiagnosticReport(items)
