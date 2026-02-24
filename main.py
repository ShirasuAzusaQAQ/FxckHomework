from __future__ import annotations

import argparse
import os
import threading
import traceback
from pathlib import Path
from tkinter import END, BOTH, LEFT, RIGHT, X, Y, filedialog, messagebox
import tkinter as tk
from tkinter import ttk

from homework_ai_editor.ai_client import AIClient, AIConfig
from homework_ai_editor.answers import load_answers_file, parse_answers_text
from homework_ai_editor.docx_editor import fill_docx_homework


def build_ai_client(api_key: str, model: str, base_url: str) -> AIClient:
    return AIClient(
        AIConfig(
            api_key=api_key.strip(),
            model=model.strip() or "gpt-4.1-mini",
            base_url=base_url.strip() or "https://api.openai.com/v1",
        )
    )


def run_batch(
    input_doc: str,
    output_doc: str,
    answers_text: str = "",
    answers_file: str = "",
    auto_solve_missing: bool = False,
    api_key: str = "",
    model: str = "gpt-4.1-mini",
    base_url: str = "https://api.openai.com/v1",
    log=print,
) -> None:
    answers = {}
    if answers_file:
        answers.update(load_answers_file(answers_file))
        log(f"已从答案文件载入 {len(answers)} 条答案。")
    if answers_text.strip():
        inline_answers = parse_answers_text(answers_text)
        answers.update(inline_answers)
        log(f"已从文本框解析 {len(inline_answers)} 条答案。")

    ai_client = None
    if auto_solve_missing:
        if not api_key.strip():
            raise ValueError("启用自动解题时必须提供 API Key。")
        ai_client = build_ai_client(api_key, model, base_url)

    def answer_provider(qid: str, question_text: str) -> str:
        if not ai_client:
            return ""
        return ai_client.solve_question(question_text)

    fill_docx_homework(
        input_path=input_doc,
        output_path=output_doc,
        answers=answers,
        answer_provider=answer_provider if auto_solve_missing else None,
        log=log,
    )
    log(f"已保存输出文档: {output_doc}")


class HomeworkApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("AI 作业文档编辑器")
        self.geometry("900x700")
        self._build_ui()

    def _build_ui(self) -> None:
        root = ttk.Frame(self, padding=10)
        root.pack(fill=BOTH, expand=True)

        self.input_var = tk.StringVar()
        self.output_var = tk.StringVar()
        self.answers_file_var = tk.StringVar()
        self.api_key_var = tk.StringVar(value=os.getenv("OPENAI_API_KEY", ""))
        self.model_var = tk.StringVar(value="gpt-4.1-mini")
        self.base_url_var = tk.StringVar(value="https://api.openai.com/v1")
        self.auto_solve_var = tk.BooleanVar(value=True)

        self._file_row(root, "输入作业(.docx)", self.input_var, self._pick_input)
        self._file_row(root, "输出文档(.docx)", self.output_var, self._pick_output)
        self._file_row(root, "答案文件(可选)", self.answers_file_var, self._pick_answers_file)

        form = ttk.Frame(root)
        form.pack(fill=X, pady=(8, 8))

        self._labeled_entry(form, "API Key", self.api_key_var, show="*")
        self._labeled_entry(form, "Model", self.model_var)
        self._labeled_entry(form, "Base URL", self.base_url_var)

        ttk.Checkbutton(form, text="缺失答案时自动调用 AI 解题", variable=self.auto_solve_var).pack(
            anchor="w", pady=(4, 0)
        )

        ttk.Label(root, text="手动输入答案（支持 `1=...` / `2: ...` / `3. ...`）").pack(anchor="w")
        self.answers_text = tk.Text(root, height=12)
        self.answers_text.pack(fill=BOTH, expand=False, pady=(4, 8))

        button_row = ttk.Frame(root)
        button_row.pack(fill=X, pady=(0, 8))
        ttk.Button(button_row, text="开始处理", command=self._start_process).pack(side=LEFT)
        ttk.Button(button_row, text="清空日志", command=self._clear_log).pack(side=LEFT, padx=(8, 0))

        ttk.Label(root, text="运行日志").pack(anchor="w")
        self.log_text = tk.Text(root, height=14)
        self.log_text.pack(fill=BOTH, expand=True)

    def _labeled_entry(self, parent: ttk.Frame, label: str, var: tk.StringVar, show: str | None = None) -> None:
        row = ttk.Frame(parent)
        row.pack(fill=X, pady=2)
        ttk.Label(row, text=label, width=12).pack(side=LEFT)
        entry = ttk.Entry(row, textvariable=var, show=show or "")
        entry.pack(side=LEFT, fill=X, expand=True)

    def _file_row(self, parent: ttk.Frame, label: str, var: tk.StringVar, command) -> None:
        row = ttk.Frame(parent)
        row.pack(fill=X, pady=2)
        ttk.Label(row, text=label, width=16).pack(side=LEFT)
        ttk.Entry(row, textvariable=var).pack(side=LEFT, fill=X, expand=True, padx=(0, 6))
        ttk.Button(row, text="选择", command=command).pack(side=RIGHT)

    def _pick_input(self) -> None:
        path = filedialog.askopenfilename(filetypes=[("Word 文档", "*.docx")])
        if path:
            self.input_var.set(path)
            if not self.output_var.get():
                p = Path(path)
                self.output_var.set(str(p.with_name(f"{p.stem}_已完成{p.suffix}")))

    def _pick_output(self) -> None:
        path = filedialog.asksaveasfilename(defaultextension=".docx", filetypes=[("Word 文档", "*.docx")])
        if path:
            self.output_var.set(path)

    def _pick_answers_file(self) -> None:
        path = filedialog.askopenfilename(filetypes=[("答案文件", "*.txt *.json"), ("所有文件", "*.*")])
        if path:
            self.answers_file_var.set(path)

    def _append_log(self, msg: str) -> None:
        self.log_text.insert(END, msg + "\n")
        self.log_text.see(END)
        self.update_idletasks()

    def _clear_log(self) -> None:
        self.log_text.delete("1.0", END)

    def _start_process(self) -> None:
        input_doc = self.input_var.get().strip()
        output_doc = self.output_var.get().strip()
        if not input_doc or not output_doc:
            messagebox.showerror("错误", "请先选择输入和输出文档。")
            return

        def worker() -> None:
            try:
                self._append_log("开始处理作业文档...")
                run_batch(
                    input_doc=input_doc,
                    output_doc=output_doc,
                    answers_text=self.answers_text.get("1.0", END),
                    answers_file=self.answers_file_var.get().strip(),
                    auto_solve_missing=self.auto_solve_var.get(),
                    api_key=self.api_key_var.get(),
                    model=self.model_var.get(),
                    base_url=self.base_url_var.get(),
                    log=lambda m: self.after(0, self._append_log, m),
                )
                self.after(0, lambda: messagebox.showinfo("完成", f"处理完成\n{output_doc}"))
            except Exception as exc:
                tb = traceback.format_exc()
                self.after(0, self._append_log, f"出错: {exc}")
                self.after(0, self._append_log, tb)
                self.after(0, lambda: messagebox.showerror("失败", str(exc)))

        threading.Thread(target=worker, daemon=True).start()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="AI 作业文档编辑器")
    parser.add_argument("--input", help="输入 docx 文件路径")
    parser.add_argument("--output", help="输出 docx 文件路径")
    parser.add_argument("--answers-file", default="", help="答案文件路径（txt/json）")
    parser.add_argument("--answers-text", default="", help="直接传入答案文本")
    parser.add_argument("--auto-solve-missing", action="store_true", help="缺失答案时自动调用 AI")
    parser.add_argument("--api-key", default=os.getenv("OPENAI_API_KEY", ""), help="AI API Key")
    parser.add_argument("--model", default="gpt-4.1-mini", help="模型名")
    parser.add_argument("--base-url", default="https://api.openai.com/v1", help="兼容接口 Base URL")
    parser.add_argument("--no-gui", action="store_true", help="强制不启动 GUI（CLI 模式）")
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if not args.no_gui and not (args.input and args.output):
        app = HomeworkApp()
        app.mainloop()
        return

    if not args.input or not args.output:
        parser.error("CLI 模式需要提供 --input 和 --output")

    run_batch(
        input_doc=args.input,
        output_doc=args.output,
        answers_text=args.answers_text,
        answers_file=args.answers_file,
        auto_solve_missing=args.auto_solve_missing,
        api_key=args.api_key,
        model=args.model,
        base_url=args.base_url,
        log=print,
    )


if __name__ == "__main__":
    main()

