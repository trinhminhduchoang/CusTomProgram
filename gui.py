"""Simple desktop interface for testing the traffic-law search."""

import math
import os
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, ttk

from law_store import LawStore, describe


NOT_FOUND_MESSAGE = "Mình không tìm thấy quy định phù hợp trong dữ liệu hiện có."


class TrafficLawGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Tra cứu luật giao thông")
        self.root.minsize(720, 560)

        self.data_dir = tk.StringVar(value=str(Path(__file__).resolve().parent / "data"))
        self.threshold = tk.StringVar(value="0.15")
        self.keyword_weight = tk.StringVar()
        self.question = tk.StringVar()
        self.status = tk.StringVar(value="Đang nạp dữ liệu...")
        self.store = None
        self.store_config = None

        self._build_layout()
        self._load_store()
        self.question_entry.focus_set()

    def _build_layout(self):
        main = ttk.Frame(self.root, padding=16)
        main.pack(fill=tk.BOTH, expand=True)
        main.columnconfigure(0, weight=1)
        main.rowconfigure(5, weight=1)

        ttk.Label(main, text="Tra cứu luật giao thông", font=("Segoe UI", 18, "bold")).grid(
            row=0, column=0, sticky="w"
        )
        ttk.Label(main, text="Nhập câu hỏi để xem quy định phù hợp trong kho dữ liệu.").grid(
            row=1, column=0, sticky="w", pady=(2, 12)
        )

        folder_row = ttk.Frame(main)
        folder_row.grid(row=2, column=0, sticky="ew", pady=(0, 8))
        folder_row.columnconfigure(1, weight=1)
        ttk.Label(folder_row, text="Thư mục dữ liệu:").grid(row=0, column=0, padx=(0, 8))
        ttk.Entry(folder_row, textvariable=self.data_dir).grid(row=0, column=1, sticky="ew")
        ttk.Button(folder_row, text="Chọn...", command=self._browse_data).grid(
            row=0, column=2, padx=(8, 0)
        )
        ttk.Button(folder_row, text="Nạp lại", command=self._load_store).grid(
            row=0, column=3, padx=(8, 0)
        )

        options = ttk.Frame(main)
        options.grid(row=3, column=0, sticky="w", pady=(0, 10))
        ttk.Label(options, text="Ngưỡng từ chối:").pack(side=tk.LEFT)
        ttk.Entry(options, textvariable=self.threshold, width=8).pack(side=tk.LEFT, padx=(6, 18))
        ttk.Label(options, text="Trọng số keywords (để trống = v0/v1):").pack(side=tk.LEFT)
        ttk.Entry(options, textvariable=self.keyword_weight, width=8).pack(
            side=tk.LEFT, padx=(6, 0)
        )

        question_row = ttk.Frame(main)
        question_row.grid(row=4, column=0, sticky="ew", pady=(0, 10))
        question_row.columnconfigure(0, weight=1)
        self.question_entry = ttk.Entry(question_row, textvariable=self.question)
        self.question_entry.grid(row=0, column=0, sticky="ew")
        self.question_entry.bind("<Return>", self._on_enter)
        ttk.Button(question_row, text="Tra cứu", command=self._search).grid(
            row=0, column=1, padx=(8, 0)
        )
        ttk.Button(question_row, text="Xóa", command=self._clear).grid(
            row=0, column=2, padx=(8, 0)
        )

        output_frame = ttk.Frame(main)
        output_frame.grid(row=5, column=0, sticky="nsew")
        output_frame.columnconfigure(0, weight=1)
        output_frame.rowconfigure(0, weight=1)
        self.output = tk.Text(output_frame, wrap=tk.WORD, state=tk.DISABLED, height=16)
        self.output.grid(row=0, column=0, sticky="nsew")
        scrollbar = ttk.Scrollbar(output_frame, orient=tk.VERTICAL, command=self.output.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.output.configure(yscrollcommand=scrollbar.set)

        ttk.Label(main, textvariable=self.status, anchor="w").grid(
            row=6, column=0, sticky="ew", pady=(8, 0)
        )

    def _browse_data(self):
        folder = filedialog.askdirectory(initialdir=self.data_dir.get() or os.getcwd())
        if folder:
            self.data_dir.set(folder)
            self._load_store()

    def _current_config(self):
        weight_text = self.keyword_weight.get().strip()
        weight = None if not weight_text else float(weight_text)
        if weight is not None and (not math.isfinite(weight) or weight < 0):
            raise ValueError("Trọng số keywords phải là số hữu hạn không âm.")
        return os.path.abspath(os.path.expanduser(self.data_dir.get().strip())), weight

    def _load_store(self):
        try:
            data_dir, weight = self._current_config()
        except ValueError as exc:
            self.status.set(f"Tham số không hợp lệ: {exc}")
            return
        if not os.path.isdir(data_dir):
            self._show_text(f"Không tìm thấy thư mục dữ liệu:\n{data_dir}")
            self.status.set("Thư mục dữ liệu không tồn tại.")
            return
        try:
            new_store = LawStore(data_dir, keyword_weight=weight)
        except (OSError, ValueError) as exc:
            self._show_text(f"Không thể nạp dữ liệu:\n{exc}")
            self.status.set("Nạp dữ liệu thất bại.")
            return

        old_store = self.store
        self.store = new_store
        self.store_config = (data_dir, weight)
        if old_store is not None:
            old_store.stop_watching()

        stats = new_store.stats()
        mode = "gộp keywords" if weight is None else f"keywords riêng, trọng số {weight:g}"
        self.status.set(
            f"{stats['records']} quy định | phiên bản kho {stats['version']} | "
            f"{mode} | {data_dir}"
        )
        messages = []
        if stats["warnings"]:
            messages.extend("Cảnh báo: " + warning for warning in stats["warnings"])
        if stats["errors"]:
            messages.extend(f"Lỗi {path}: {message}" for path, message in stats["errors"].items())
        if messages:
            self._show_text("\n".join(messages))
        else:
            self._show_text("Dữ liệu đã sẵn sàng. Hãy nhập câu hỏi để bắt đầu.")

    def _search(self):
        question = self.question.get().strip()
        if not question:
            self.status.set("Hãy nhập câu hỏi trước khi tra cứu.")
            self.question_entry.focus_set()
            return

        try:
            config = self._current_config()
        except ValueError:
            self.status.set("Trọng số keywords không hợp lệ.")
            return
        if self.store is None or config != self.store_config:
            self._load_store()
            if self.store is None or config != self.store_config:
                return

        try:
            threshold = float(self.threshold.get())
        except ValueError:
            self.status.set("Ngưỡng từ chối phải là một số không âm.")
            return
        if not math.isfinite(threshold) or threshold < 0:
            self.status.set("Ngưỡng từ chối phải là số hữu hạn không âm.")
            return

        results = self.store.search(question, top_k=3)
        shown = [result for result in results if result["score"] >= threshold]
        if not shown:
            self._show_text(NOT_FOUND_MESSAGE)
            self.status.set("Không có kết quả vượt ngưỡng đã chọn.")
            return

        lines = []
        for index, result in enumerate(shown):
            title = "Kết quả phù hợp nhất" if index == 0 else f"Kết quả liên quan {index + 1}"
            lines.append(f"{title}  |  điểm: {result['score']:.3f}")
            lines.append(describe(result["record"]))
            lines.append("")
        lines.append("Thông tin chỉ mang tính tham khảo, không phải tư vấn pháp lý.")
        self._show_text("\n".join(lines))
        self.status.set(f"Tìm thấy {len(shown)} kết quả (ngưỡng {threshold:.2f}).")

    def _clear(self):
        self.question.set("")
        self._show_text("")
        self.status.set("Đã xóa kết quả.")
        self.question_entry.focus_set()

    def _show_text(self, text):
        self.output.configure(state=tk.NORMAL)
        self.output.delete("1.0", tk.END)
        self.output.insert("1.0", text)
        self.output.configure(state=tk.DISABLED)

    def _on_enter(self, _event):
        self._search()
        return "break"

    def close(self):
        if self.store is not None:
            self.store.stop_watching()
        self.root.destroy()


def main():
    root = tk.Tk()
    app = TrafficLawGUI(root)
    root.protocol("WM_DELETE_WINDOW", app.close)
    root.mainloop()


if __name__ == "__main__":
    main()
