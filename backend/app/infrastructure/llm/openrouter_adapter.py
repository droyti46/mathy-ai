import base64, json, anyio
from typing import Sequence, Dict, Any
from openai import OpenAI
from app.application.interfaces.llm import ILLM
from app.settings import Settings
import re
import json

def _safe_json(s: str) -> Dict[str, Any]:
    try:
        return json.loads(s)
    except Exception:
        return {"summary": s.strip()[:1500], "spans": []}

class OpenRouterAdapter(ILLM):
    def __init__(self, settings: Settings):
        self.s = settings
        self.client = OpenAI(
            base_url=self.s.OPENROUTER_BASE_URL,
            api_key=self.s.OPENROUTER_API_KEY,
            default_headers={"HTTP-Referer": "http://localhost:8000", "X-Title": self.s.APP_NAME},
        )

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
            "You are a strict math grader. Output ONLY JSON with keys:",
            '{"summary": "str", "spans": [{"start": 0, "end": 1, "message": "str", "severity": "error"|"warning"}]}',
            "Indices refer to character positions in USER_SOLUTION.",
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
        system = "You are a helpful tutor. Give a HINT only. Do NOT reveal the final numeric answer or the full solution."
        messages = [{"role": "system", "content": system}]
        messages += [{"role": m["role"], "content": m["content"]} for m in chat_history]
        messages.append({"role": "user", "content": f"Task context:\n{task}"})
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
            "You are a strict math grader. "
            "Return ONLY JSON with keys: summary (string), "
            "spans (list of [start,end] integer pairs pointing to mistakes in the student's solution), "
            "score (0..1, optional). "
            "Never reveal the final numeric answer; provide formative feedback."
        )
        user = (
            f"Task:\n{task_md}\n\n"
            f"Student solution (plain text):\n{solution_text}\n\n"
            f"Reference solution (optional):\n{reference}"
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
            data = {"summary": text[:500], "spans": []}

        # нормализуем spans к [[a,b],...]
        norm_spans = []
        raw_spans = data.get("spans", [])
        for item in raw_spans:
            if isinstance(item, dict):
                norm_spans.append([int(item.get("start", 0)), int(item.get("end", 0))])
            elif isinstance(item, (list, tuple)) and len(item) >= 2:
                norm_spans.append([int(item[0]), int(item[1])])
        data["spans"] = norm_spans
        return data