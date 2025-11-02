import base64
import json

import anyio
from typing import Sequence, Dict, Any
from openai import OpenAI
from app.infrastructure.prompts.text_store import PromptTextStore
from app.application.interfaces.llm import ILLM
from app.settings import Settings 
import re

def _safe_json(s: str) -> Dict[str, Any]:
    try:
        return json.loads(s)
    except Exception:
        return {"summary": s.strip()[:1500]}

class OpenRouterAdapter(ILLM):
    def __init__(self, settings: Settings):
        self.s = settings
        self.client = OpenAI(
            base_url=self.s.OPENROUTER_BASE_URL,
            api_key=self.s.OPENROUTER_API_KEY,
            default_headers={"HTTP-Referer": "http://localhost:8000", "X-Title": self.s.APP_NAME},
        )
        self.prompts = PromptTextStore(base_dir="app/infrastructure/prompts")

    async def _chat(self, messages, model: str, response_format: Dict[str, Any] | None = None) -> str:
        def _do():
            kwargs: Dict[str, Any] = {}
            if response_format:
                kwargs["response_format"] = response_format
            return self.client.chat.completions.create(model=model, messages=messages, **kwargs)
        resp = await anyio.to_thread.run_sync(_do)
        return resp.choices[0].message.content or ""

    async def check_solution(self, task: str, user_solution: str) -> Dict[str, Any]:
        system_lines = [
            "You are a strict math grader. Output ONLY JSON with a single key 'summary' (string).",
            "No extra text outside JSON.",
        ]
        system = "\n".join(system_lines)
        user = f"TASK:\n{task}\n---\nUSER_SOLUTION:\n{user_solution}"
        rf = {"type": "json_object"} if self.s.STRICT_JSON else None
        out = await self._chat(
            [{"role": "system", "content": system}, {"role": "user", "content": user}],
            model=self.s.LLM_MODEL_CHECK, response_format=rf,
        )
        return _safe_json(out)

    async def hint(self, task: str, chat_history: Sequence[Dict[str, str]]) -> str:
        # system = (
        #     "You are a vigilant math tutor. Analyse the student's reasoning, point out where the mistake occurs, "
        #     "and suggest how to fix the approach. Under no circumstances provide the correct final answer or a full solution."
        # )
        # messages = [{"role": "system", "content": system}]
        # messages += [{"role": m["role"], "content": m["content"]} for m in chat_history]
        # messages.append({"role": "user", "content": f"Task context:\n{task}"})
        messages = self.prompts.build(
            "assistant",
            chat_history=chat_history,
            wrap_user=[0],
            user_var="input"
        )
        print(messages)
        return await self._chat(messages, model=self.s.LLM_MODEL_HINT)

    async def solve(self, task: str) -> str:
        system = "You are an expert math teacher. Provide a complete step-by-step solution in Markdown."
        return await self._chat([{"role": "system", "content": system}, {"role": "user", "content": task}], model=self.s.LLM_MODEL_SOLVE)

    async def image_to_text_bytes(self, image_bytes: bytes, mime: str = "image/png") -> str:
        b64 = base64.b64encode(image_bytes).decode("ascii")
        content = [
            {"type": "text", "text": "Extract the student's handwritten solution as plain text. No comments, no formatting."},
            {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{b64}"}},
        ]
        def _do():
            return self.client.chat.completions.create(model=self.s.LLM_MODEL_VISION, messages=[{"role": "user", "content": content}])
        resp = await anyio.to_thread.run_sync(_do)
        return (resp.choices[0].message.content or "").strip()
    
    async def grade(self, task_md: str, solution_text: str, reference: str = "") -> dict:
        system = (
            "Ты математический проверяющий. "
            "Верни ТОЛЬКО JSON с ключами: summary (строка) и score (от 0 до 1, необязательный). "
            "Не раскрывай конечный числовой ответ; дай содержательную обратную связь."
        )

        user = (
            f"Задача:\n{task_md}\n\n"
            f"Решение студента (текст):\n{solution_text}\n\n"
            f"Эталонное решение (необязательно):\n{reference}\n\n"
            "Отметь только действительно значимые ошибки — неверные шаги рассуждений, пропущенные случаи или неверные формулы."
        )

        # выберем модель для градинга: LLM_MODEL_GRADE если есть, иначе LLM_MODEL_CHECK
        model = getattr(self.s, "LLM_MODEL_GRADE", None) or self.s.LLM_MODEL_CHECK
        rf = {"type": "json_object"} if getattr(self.s, "STRICT_JSON", False) else None

        text = await self._chat(
            [
                {"role": "system", "content": system},
                {"role": "user",  "content": user},
            ],
            model=model,
            response_format=rf,
        )

        # вытащим JSON из возможного текста вокруг
        m = re.search(r"\{.*\}", text, re.S)
        blob = m.group(0) if m else text
        try:
            data = json.loads(blob)
        except Exception:
            data = {"summary": text[:500]}

        # Если модель всё же вернула spans, аккуратно нормализуем, иначе удалим ключ.
        raw_spans = data.get("spans")
        if raw_spans:
            norm_spans = []
            for item in raw_spans:
                if isinstance(item, dict):
                    norm_spans.append([int(item.get("start", 0)), int(item.get("end", 0))])
                elif isinstance(item, (list, tuple)) and len(item) >= 2:
                    norm_spans.append([int(item[0]), int(item[1])])
            if norm_spans:
                data["spans"] = norm_spans
            else:
                data.pop("spans", None)
        else:
            data.pop("spans", None)

        return data
