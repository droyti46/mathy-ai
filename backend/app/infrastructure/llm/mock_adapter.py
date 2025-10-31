import re
from typing import Dict, Any, Sequence

class MockLLM:
    async def check_solution(self, task: str, user_solution: str) -> Dict[str, Any]:
        spans = []
        if len(user_solution.strip()) == 0:
            summary = "Похоже, решение пустое. Попробуйте описать ход мыслей."
        else:
            summary = "Нашёл потенциальные неточности. Проверьте выделенные места."
            m = re.search(r"(?:ответ|равно|=)\s*\d+", user_solution, re.IGNORECASE)
            if m:
                spans.append({"start": int(m.start()), "end": int(m.end()), "message": "Слишком рано получили численный ответ. Обоснуйте шаги.", "severity": "warning"})
        return {"summary": summary, "spans": spans}

    async def hint(self, task: str, chat_history: Sequence[dict]) -> str:
        return (
            "Похоже, в одном из шагов нарушена логика вывода. Найдите место, где делаете допущение, и перепроверьте его. "
            "Не вычисляйте окончательный ответ, пока не убедитесь, что переход обоснован."
        )

    async def solve(self, task: str) -> str:
        return "### Решение (mock)\nЭтот адаптер-заглушка показывает, где будет полное решение. Подключите OpenRouter в .env."
