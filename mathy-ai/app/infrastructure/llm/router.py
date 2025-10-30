from typing import Optional
from app.application.interfaces.llm import ILLM
from app.settings import Settings
from .openrouter_adapter import OpenRouterAdapter
from .mock_adapter import MockLLM
import httpx
from fastapi import HTTPException

def _strip_code_fences(text: str) -> str:
    t = (text or "").strip()
    if t.startswith("```") and t.endswith("```"):
        lines = t.splitlines()
        # убираем первую и последнюю строку с ```
        if len(lines) >= 2:
            return "\n".join(lines[1:-1]).strip()
    return t

class LLMRouter(ILLM):
    def __init__(self, adapter, settings: Settings):
        self.adapter = adapter
        self.settings = settings
        self.mock = bool(getattr(settings, "MOCK_LLM", False))

    async def hint_from_text(self, statement_md: str, student_text: str, level: int = 1) -> str:
        level_msg = {
            1: "Дай очень мягкую наводку на следующий шаг без разглашения конечного ответа.",
            2: "Дай более конкретный намёк (формула/правило), но без финального результата.",
            3: "Опиши почти весь путь решения, но не подставляй финальное число/выражение.",
        }[level if level in (1,2,3) else 1]

        messages = [
            {"role": "system", "content": "Ты даёшь краткие полезные подсказки, не раскрывая конечный ответ."},
            {"role": "user", "content": f"УСЛОВИЕ:\n{statement_md}\n\nОТВЕТ СТУДЕНТА:\n{student_text}\n\n{level_msg}"},
        ]
        return await self._chat_text(messages=messages, model=self.settings.LLM_MODEL_HINT, temperature=0)


    async def solve(self, task_md: str):
        if self.mock:
            return {
                "steps": [{"title": "Идея", "content_md": "Мок-решение. Опишите ключевой приём..."}],
                "final_answer_md": "_Ответ:_ ... (мок)"
            }
        if hasattr(self.adapter, "solve"):
            return await self.adapter.solve(task_md)
        raise NotImplementedError("Adapter.solve is missing")

    async def grade(self, task_md: str, solution_text: str, reference: Optional[str] = "") -> dict:
        """
        Возвращает dict:
          - summary: str
          - spans: list[[start,end], ...]
          - score: float | None
        """
        if self.mock:
            spans = [[0, min(8, len(solution_text))]] if solution_text else []
            return {"summary": "Mock grading (LLM disabled).", "spans": spans, "score": None}

        if hasattr(self.adapter, "grade"):
            return await self.adapter.grade(task_md, solution_text, reference or "")

        if hasattr(self.adapter, "grade_fallback"):
            return await self.adapter.grade_fallback(task_md, solution_text, reference or "")

        raise NotImplementedError("Adapter.grade is missing")

    @classmethod
    def from_settings(cls, s: Settings) -> "LLMRouter":
        # ВАЖНО: передаём и adapter, и settings
        impl = OpenRouterAdapter(s) if s.OPENROUTER_API_KEY else MockLLM()
        return cls(impl, s)

    # Эти методы должны дергать adapter, а не несуществующий impl
    async def check_solution(self, task: str, user_solution: str):
        if hasattr(self.adapter, "check_solution"):
            return await self.adapter.check_solution(task, user_solution)
        raise NotImplementedError("Adapter.check_solution is missing")

    async def image_to_text_bytes(self, image_bytes: bytes, mime: str = "image/png") -> str:
        if hasattr(self.adapter, "image_to_text_bytes"):
            return await self.adapter.image_to_text_bytes(image_bytes, mime)
        return ""
    
    # внутри LLMRouter
    PROMPT_MARK_ERRORS_RU = """# РОЛЬ
    Строгий математический проверяющий.

    # ЗАДАЧА
    Найди все ошибки и отметь все производные от них ошибки.

    # ВЫВОД
    Верни исходный текст решения задачи без изменений, добавив только теги <w>...</w> вокруг ошибочных фрагментов. Никаких комментариев.

    # ПРАВИЛА
    1) Размечай минимальный неверный фрагмент (число, знак, слово или часть выражения). Пример: если фраза "они получаются вещественными" неверна, выдели только ключевое слово <w>вещественными</w>.
    2) Если ошибка логически тянет за собой другие (производные) — пометь их тоже, даже если нарушается минимальность. Выделить производные ошибки важнее, чем соблюдать минимальность.
    3) Если левая часть уравнения или преобразования содержит помеченный фрагмент, пометь и правую часть равенства/преобразования (число, выражение, десятичную запись, округление), даже если вычисление само по себе верное.
    4) Если число/символ помечено, пометь все его дальнейшие появления и все числовые результаты, полученные из него.
    5) Разложения и тождества: помечай любой лишний или неправильно разложенный член (например, в тригонометрических формулах) и все последствия от неправильного разложения.
    6) Нормализация степеней/масштабов: при выносе и замене помечай неверные степени и все зависящие от них результаты.
    7) Пространство исходов/мощности: если неверно выбран базовый счёт (например, «по m вариантов»), пометь и производные мощности/значения (m^3, итоги).
    8) Не меняй форматирование, пробелы, переносы строк и сам текст.
    9) Не выделяй введение обозначений. То есть, если x ошибочен, и написано "пусть a = x / 2", мы не выделяем эту запись тегами. Выделяй такие записи, только если в них уже производится численная подстановка или логически неверное равенство.

    # ИЛЛЮСТРАЦИИ ФОРМАТА
    Было:  2+2=5.
    Стало: 2+2=<w>5</w>.

    Было:  sin(a+b) = sin a cos b + cos a sin b + sin a sin b.
    Стало:  sin(a+b) = sin a cos b + cos a sin b + <w>sin a sin b</w>.

    Было:  x = 3. Тогда, возведём x в квадрат: x^2 = 16.
    Стало:  x = 3. Тогда, возведём x в квадрат: x^2 = <w>16</w>.
    """

    async def _chat_text(self, *, messages: list[dict], model: str, temperature: float = 0.0, max_tokens: int | None = None) -> str:
        """
        Универсальный текстовый вызов Chat Completions. Возвращает content как строку.
        """
        url = f"{self.settings.OPENROUTER_BASE_URL.rstrip('/')}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.settings.OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://example.com",
            "X-Title": "Math Trainer",
        }
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
        }
        if max_tokens is not None:
            payload["max_tokens"] = max_tokens

        try:
            async with httpx.AsyncClient(timeout=120, http2=True, trust_env=True) as client:
                resp = await client.post(url, headers=headers, json=payload)
        except httpx.HTTPError as exc:
            raise HTTPException(status_code=502, detail=f"LLM connect error: {type(exc).__name__}: {exc}") from exc

        if resp.status_code >= 400:
            raise HTTPException(status_code=502, detail=f"LLM upstream error: {resp.status_code} {resp.text}")

        data = resp.json()
        # Иногда приходит с индексом-строкой "0", иногда как список
        content = None
        if isinstance(data.get("choices"), dict):
            content = data["choices"].get("0", {}).get("message", {}).get("content")
        elif isinstance(data.get("choices"), list) and data["choices"]:
            content = data["choices"][0].get("message", {}).get("content")

        if content is None:
            raise HTTPException(status_code=502, detail=f"LLM bad response: {data}")

        return _strip_code_fences(content)

    async def mark_errors(self, statement_md: str, student_text: str) -> str:
        """
        Возвращает исходный текст student's solution с размеченными тегами <w>...</w>.
        Никаких комментариев, только сам текст с тегами.
        """
        messages = [
            {"role": "system", "content": "Возвращай ТОЛЬКО исходный текст решения с тегами <w>...</w>. Никаких комментариев."},
            {"role": "user", "content": (
                f"{self.PROMPT_MARK_ERRORS_RU if hasattr(self,'PROMPT_MARK_ERRORS_RU') else self.PROMPT_MARK_ERRORS_RU}\n\n"
                f"# УСЛОВИЕ\n{statement_md.strip()}\n\n"
                "# РЕШЕНИЕ (верни этот текст без изменений, добавив только <w>...>):\n"
                f"{student_text}"
            )},
        ]
        # ВАЖНО: здесь нужен именно ТЕКСТОВЫЙ ответ (не JSON)
        return await self._chat_text(messages=messages, model=self.settings.LLM_MODEL_CHECK, temperature=0)

