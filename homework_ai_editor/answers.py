from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Dict


ANSWER_LINE_PATTERNS = [
    re.compile(r"^\s*题?\s*(\d+)\s*[=:：]\s*(.+?)\s*$"),
    re.compile(r"^\s*(\d+)\s*[=:：]\s*(.+?)\s*$"),
    re.compile(r"^\s*(\d+)\s*[\.、]\s*(.+?)\s*$"),
]


def parse_answers_text(text: str) -> Dict[str, str]:
    answers: Dict[str, str] = {}
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        for pattern in ANSWER_LINE_PATTERNS:
            match = pattern.match(line)
            if match:
                qid, answer = match.groups()
                answers[str(int(qid))] = answer.strip()
                break
    return answers


def load_answers_file(path: str | Path) -> Dict[str, str]:
    file_path = Path(path)
    if not file_path.exists():
        raise FileNotFoundError(f"答案文件不存在: {file_path}")

    if file_path.suffix.lower() == ".json":
        data = json.loads(file_path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise ValueError("JSON 答案文件必须是对象格式，例如 {\"1\": \"答案\"}")
        return {str(int(k)): str(v).strip() for k, v in data.items() if str(v).strip()}

    return parse_answers_text(file_path.read_text(encoding="utf-8"))

