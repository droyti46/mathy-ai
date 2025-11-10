import base64
import json

import anyio
from typing import Sequence, Dict, Any, Optional, AsyncGenerator
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
        self.openrouter_client = OpenAI(
            base_url=self.s.OPENROUTER_BASE_URL,
            api_key=self.s.OPENROUTER_API_KEY,
            default_headers={"HTTP-Referer": "http://localhost:8000", "X-Title": self.s.APP_NAME},
        )
        self.nscale_client = OpenAI(
            base_url=self.s.NSCALE_BASE_URL,
            api_key=self.s.NSCALE_SERVICE_TOKEN,
        )
        self.prompts = PromptTextStore(base_dir="app/infrastructure/prompts")

    async def _stream_chat(self, *, messages, model: str) -> AsyncGenerator[str, None]:
        """
        Асинхронный генератор, выдающий токены текста по мере генерации.
        Реализовано через stream=True в openai sdk + мост через anyio.
        """
        send, recv = anyio.create_memory_object_stream[str](max_buffer_size=200)

        def _producer():
            stream = self.openrouter_client.chat.completions.create(
                model=model,
                messages=messages,
                stream=True,
            )
            try:
                for ev in stream:
                    # OpenAI совместимый формат
                    delta: Optional[str] = None
                    try:
                        delta = ev.choices[0].delta.content
                    except Exception:
                        delta = None
                    if delta:
                        anyio.from_thread.run(send.send, delta)
            finally:
                anyio.from_thread.run(send.aclose)

        # крутим продьюсер в отдельном потоке
        async with anyio.create_task_group() as tg:
            tg.start_soon(anyio.to_thread.run_sync, _producer)
            async with recv:
                async for chunk in recv:
                    yield chunk

    async def _chat(
        self,
        messages,
        model: str,
        response_format: Dict[str, Any] | None = None,
        *,
        use_nscale: bool = False,
    ) -> str:
        def _do():
            kwargs: Dict[str, Any] = {}
            if response_format:
                kwargs["response_format"] = response_format
            client = self.nscale_client if use_nscale else self.openrouter_client
            return client.chat.completions.create(model=model, messages=messages, **kwargs)
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
            model=self.s.LLM_MODEL_CHECK,
            response_format=rf,
        )
        return _safe_json(out)

    async def hint(self, task: str, chat_history: Sequence[Dict[str, str]]) -> str:
        messages = self.prompts.build(
            "assistant",
            chat_history=chat_history,
            vars={'task': task},
            wrap_user=[0],
            user_var="input"
        )
        return await self._chat(messages, model=self.s.LLM_MODEL_ASSISTANT)
    
    async def init_teacher_mode(self, task: str) -> str:
        '''Инициализирует режим преподавания'''
        messages = self.prompts.build(
            "teacher",
            vars={'task': task}
        )

        return await self._chat(messages, model=self.s.LLM_MODEL_CHECK)
    
    async def teacher_message(self, task: str, chat_history: Sequence[Dict[str, str]]) -> str:
        messages = self.prompts.build(
            "teacher",
            chat_history=chat_history,
            vars={"task": task},
            wrap_user=[0],
        )
        return await self._chat(messages, model=self.s.LLM_MODEL_ASSISTANT)

    async def solve(self, task: str) -> str:
        """Решает задание"""
        messages = self.prompts.build(
            "solver",
            vars={'task': task},
            wrap_user="all"
        )
        return await self._chat(messages, model=self.s.NSCALE_MODEL_SOLVE, use_nscale=True)

    async def image_to_text_bytes(self, image_bytes: bytes, mime: str = "image/png") -> str:
        b64 = base64.b64encode(image_bytes).decode("ascii")
        content = [
            {"type": "text", "text": "Extract the student's handwritten solution as plain text. No comments, no formatting."},
            {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{b64}"}},
        ]
        def _do():
            return self.openrouter_client.chat.completions.create(
                model=self.s.LLM_MODEL_VISION, messages=[{"role": "user", "content": content}]
            )
        resp = await anyio.to_thread.run_sync(_do)
        return (resp.choices[0].message.content or "").strip()
    
    async def check_solution(self, task_md: str, solution_text: str) -> dict:
        '''Проверяет решение студента и возвращает размеченное решение студента с тегами <w message="">...</w>'''
        messages = self.prompts.build(
            "check_solution",
            vars={'task': task_md, 'solution': solution_text},
        )

        return await self._chat(messages, model=self.s.NSCALE_MODEL_CHECK, use_nscale=True)

    async def hint_stream(self, task: str, chat_history: Sequence[Dict[str, str]]) -> AsyncGenerator[str, None]:
        messages = self.prompts.build(
            "assistant", chat_history=chat_history, vars={'task': task}, wrap_user=[0], user_var="input"
        )
        async for tok in self._stream_chat(messages=messages, model=self.s.LLM_MODEL_ASSISTANT):
            yield tok

    async def init_teacher_mode_stream(self, task: str) -> AsyncGenerator[str, None]:
        messages = self.prompts.build("teacher", vars={'task': task})
        async for tok in self._stream_chat(messages=messages, model=self.s.LLM_MODEL_CHECK):
            yield tok

    async def teacher_message_stream(self, task: str, chat_history: Sequence[Dict[str, str]]) -> AsyncGenerator[str, None]:
        messages = self.prompts.build("teacher", chat_history=chat_history, vars={"task": task}, wrap_user=[0])
        async for tok in self._stream_chat(messages=messages, model=self.s.LLM_MODEL_ASSISTANT):
            yield tok

    async def solve_stream(self, task: str) -> AsyncGenerator[str, None]:
        messages = self.prompts.build("solver", vars={'task': task}, wrap_user="all")
        result = await self._chat(messages, model=self.s.NSCALE_MODEL_SOLVE, use_nscale=True)
        yield result

    @classmethod
    def from_settings(cls, s: Settings) -> "OpenRouterAdapter":
        # ВАЖНО: передаём и adapter, и settings
        return cls(s)