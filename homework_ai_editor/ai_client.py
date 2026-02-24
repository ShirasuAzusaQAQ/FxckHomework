from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import requests


@dataclass
class AIConfig:
    api_key: str
    model: str = "gpt-4.1-mini"
    base_url: str = "https://api.openai.com/v1"
    timeout_seconds: int = 60


class AIClient:
    def __init__(self, config: AIConfig):
        self.config = config

    def solve_question(self, question_text: str) -> str:
        if not self.config.api_key.strip():
            raise ValueError("缺少 API Key，无法自动解题。")

        url = f"{self.config.base_url.rstrip('/')}/chat/completions"
        system_prompt = (
            "你是一个学生作业辅助助手。请直接给出简洁、正确、适合抄写到作业中的答案。"
            "如果题目是选择题，优先给出选项和简要理由；如果是填空题，给出最终填空内容；"
            "如果是简答题，控制在适中长度。不要输出多余寒暄。"
        )
        user_prompt = f"请解答这道作业题，并给出可直接填写到作业中的答案：\n\n{question_text}"

        resp = requests.post(
            url,
            headers={
                "Authorization": f"Bearer {self.config.api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": self.config.model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                "temperature": 0.2,
            },
            timeout=self.config.timeout_seconds,
        )
        resp.raise_for_status()
        data = resp.json()

        try:
            content = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise ValueError(f"AI 返回格式异常: {data}") from exc

        if isinstance(content, list):
            text_parts = []
            for item in content:
                if isinstance(item, dict) and item.get("type") == "text":
                    text_parts.append(item.get("text", ""))
            content = "\n".join(part for part in text_parts if part)

        return str(content).strip()

