from __future__ import annotations

import os
import queue
import subprocess
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from . import __version__
from .errors import convert_error
from .diagnostics import run_diagnostics
from .pipeline import process


class TranslatorApp:
    def __init__(self) -> None:
        self.root = tk.Tk()
        self.root.title(f"Douyin AI Translator v{__version__} — Lồng tiếng AI")
        self.root.geometry("820x600")
        self.root.minsize(760, 560)
        self.events: queue.Queue = queue.Queue()
        self.source = tk.StringVar()
        self.output_dir = tk.StringVar(value=str(Path.home() / "Videos" / "Douyin_AI_Translator"))
        self.audio_mode = tk.StringVar(value="replace")
        self.hide_chinese_subtitles = tk.BooleanVar(value=True)
        self.status = tk.StringVar(value="Sẵn sàng")
        self._build()

    def _build(self) -> None:
        frame = ttk.Frame(self.root, padding=22)
        frame.pack(fill="both", expand=True)
        ttk.Label(frame, text=f"DOUYIN AI TRANSLATOR  v{__version__}", font=("Segoe UI", 20, "bold")).pack(anchor="w")
        ttk.Label(frame, text="Dịch, xóa phụ đề Trung và lồng tiếng Việt tự nhiên", font=("Segoe UI", 11)).pack(anchor="w", pady=(2, 22))

        ttk.Label(frame, text="Tệp video trong máy (khuyên dùng) hoặc liên kết:").pack(anchor="w")
        source_row = ttk.Frame(frame)
        source_row.pack(fill="x", pady=(6, 15))
        ttk.Entry(source_row, textvariable=self.source).pack(side="left", fill="x", expand=True)
        ttk.Button(source_row, text="Chọn video", command=self._choose_video).pack(side="left", padx=(8, 0))

        ttk.Label(frame, text="Thư mục lưu kết quả:").pack(anchor="w")
        output_row = ttk.Frame(frame)
        output_row.pack(fill="x", pady=(6, 20))
        ttk.Entry(output_row, textvariable=self.output_dir).pack(side="left", fill="x", expand=True)
        ttk.Button(output_row, text="Chọn thư mục", command=self._choose_output).pack(side="left", padx=(8, 0))

        ttk.Label(frame, text="Chọn cách lồng tiếng:", font=("Segoe UI", 10, "bold")).pack(anchor="w")
        mode_frame = ttk.Frame(frame)
        mode_frame.pack(fill="x", pady=(5, 12))
        ttk.Radiobutton(
            mode_frame,
            text="1. Song ngữ — giữ thoại/âm thanh gốc và lồng thêm tiếng Việt (nhanh)",
            variable=self.audio_mode,
            value="dual",
        ).pack(anchor="w", pady=2)
        ttk.Radiobutton(
            mode_frame,
            text="2. Thay thoại — bỏ thoại Trung, giữ nhạc/bối cảnh và lồng tiếng Việt (AI, chậm hơn)",
            variable=self.audio_mode,
            value="replace",
        ).pack(anchor="w", pady=2)
        ttk.Checkbutton(
            mode_frame,
            text="Che kín phụ đề Trung và thay bằng bảng phụ đề Việt rõ ràng",
            variable=self.hide_chinese_subtitles,
        ).pack(anchor="w", pady=(5, 0))

        self.progress = ttk.Progressbar(frame, maximum=100)
        self.progress.pack(fill="x", pady=(0, 8))
        ttk.Label(frame, textvariable=self.status).pack(anchor="w")

        action_row = ttk.Frame(frame)
        action_row.pack(fill="x", pady=(24, 0))
        self.start_button = ttk.Button(action_row, text="DỊCH VIDEO", command=self._start)
        self.start_button.pack(side="left", ipadx=20, ipady=7)
        ttk.Button(action_row, text="Mở thư mục kết quả", command=self._open_output).pack(side="left", padx=10, ipady=7)
        ttk.Button(action_row, text="Kiểm tra máy", command=self._check_machine).pack(side="left", ipady=7)
        ttk.Label(frame, text="Nếu ứng dụng mở Chrome riêng: không cần đăng nhập, không đóng cửa sổ; ứng dụng sẽ tự đóng.", foreground="#555").pack(anchor="w", pady=(24, 0))
        ttk.Label(frame, text="Một giọng nữ kể chuyện vui tươi; giữ trọn nghĩa, không tự cắt từ trong câu dịch.", foreground="#666").pack(anchor="w", pady=(4, 0))

    def _choose_video(self) -> None:
        selected = filedialog.askopenfilename(filetypes=[("Video", "*.mp4 *.mov *.mkv *.avi *.webm"), ("Tất cả tệp", "*.*")])
        if selected:
            self.source.set(selected)

    def _choose_output(self) -> None:
        selected = filedialog.askdirectory()
        if selected:
            self.output_dir.set(selected)

    def _open_output(self) -> None:
        folder = Path(self.output_dir.get()).expanduser()
        folder.mkdir(parents=True, exist_ok=True)
        if os.name == "nt":
            os.startfile(folder)
        else:
            subprocess.Popen(["xdg-open", str(folder)])

    def _check_machine(self) -> None:
        report = run_diagnostics(Path(self.output_dir.get()).expanduser())
        if report.passed:
            messagebox.showinfo("Kiểm tra máy", report.as_text())
        else:
            messagebox.showwarning("Máy chưa sẵn sàng", report.as_text())

    def _start(self) -> None:
        if not self.source.get().strip():
            messagebox.showerror("Thiếu nguồn video", "Bạn hãy chọn video hoặc dán liên kết trước.")
            return
        self.start_button.configure(state="disabled")
        self.progress["value"] = 0
        # Chụp cấu hình tại luồng giao diện trước khi chạy worker nền.
        self.job_source = self.source.get()
        self.job_output_dir = Path(self.output_dir.get()).expanduser()
        self.job_audio_mode = self.audio_mode.get()
        self.job_hide_subtitles = self.hide_chinese_subtitles.get()
        thread = threading.Thread(target=self._worker, daemon=True)
        thread.start()
        self.root.after(100, self._poll)

    def _worker(self) -> None:
        try:
            result = process(
                self.job_source,
                self.job_output_dir,
                lambda p, m: self.events.put(("progress", p, m)),
                hide_chinese_subtitles=self.job_hide_subtitles,
                audio_mode=self.job_audio_mode,
            )
            self.events.put(("done", result))
        except Exception as exc:
            self.events.put(("error", convert_error(exc).user_message))

    def _poll(self) -> None:
        try:
            while True:
                event = self.events.get_nowait()
                if event[0] == "progress":
                    self.progress["value"] = event[1]
                    self.status.set(event[2])
                elif event[0] == "done":
                    self.start_button.configure(state="normal")
                    result = event[1]
                    messagebox.showinfo("Hoàn thành", f"Đã tạo video tiếng Việt:\n{result.video}\n\nPhụ đề:\n{result.subtitle}")
                    return
                elif event[0] == "error":
                    self.start_button.configure(state="normal")
                    self.status.set("Xử lý thất bại")
                    messagebox.showerror("Không thể xử lý video", event[1])
                    return
        except queue.Empty:
            pass
        self.root.after(100, self._poll)

    def run(self) -> None:
        self.root.mainloop()
