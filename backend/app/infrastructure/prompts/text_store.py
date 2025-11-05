# app/infrastructure/prompts/text_store.py
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Sequence, Union, Iterable, Optional
from string import Template
import re

@dataclass
class ChatMessage:
    role: str
    content: str

class PromptTextStore:
    """
    Простой файловый стор для промптов в .txt.

    Структура на диске:
      BASE_DIR/<name>/{system.txt,user.txt,assistant.txt,tool.txt}
    или fallback:
      BASE_DIR/<name>.txt -> трактуется как system.txt

    Плейсхолдеры формата string.Template: $var или ${var}.

    Особенности:
    - system.txt добавляется как отдельное сообщение в начале (если есть).
    - user.txt теперь используется как «обёртка» для выбранных сообщений пользователя
      из chat_history, а не как самостоятельное сообщение в конце.
      Внутрь шаблона подставляется исходный текст пользователского сообщения по ключу `user_var`
      (по умолчанию 'input', то есть используйте $input в user.txt).
    - assistant.txt и tool.txt, если есть, добавляются в самом конце как есть.
    """

    _roles_order = ("system", "user", "assistant", "tool")
    _ph_re = re.compile(r"\$(?:{(?P<braced>[A-Za-z_]\w*)}|(?P<plain>[A-Za-z_]\w*))")

    def __init__(self, base_dir: str, encoding: str = "utf-8") -> None:
        self.base_dir = Path(base_dir)
        self.encoding = encoding
        self._cache: dict[Path, tuple[float, str]] = {}

    # ---------- public API ----------
    def build(
        self,
        name: str,
        *,
        vars: Dict[str, str] | None = None,
        chat_history: Optional[Sequence[Dict[str, str]]] = None,
        wrap_user: Union[str, int, Iterable[int], None] = "last",
        user_var: str = "input",
    ) -> List[Dict[str, str]]:
        """
        Собирает messages для LLM.

        Параметры:
          - vars: словарь для подстановок в шаблоны (.txt), кроме обёртки user.
          - chat_history: уже имеющаяся история (role/content).
          - wrap_user:
              "last"  -> обернуть последнего user-а (по умолчанию),
              "all"   -> обернуть всех user-ов,
              int     -> обернуть user по индексу (0..N-1, поддерживаются отрицательные индексы),
              [int...]-> обернуть конкретные индексы,
              None    -> никого не оборачивать.
          - user_var: имя плейсхолдера в user.txt, куда попадёт исходный текст пользователя.
                      Например, если user_var="query", используйте $query в user.txt.

        Возвращает:
          список словарей {role, content}.
        """
        vars = vars or {}
        templates = self._load_templates(name)
        messages: List[Dict[str, str]] = []

        # 1) system (если есть)
        if "system" in templates:
            messages.append({"role": "system", "content": self._render(templates["system"], vars)})

        # 2) подготовим набор индексов user-сообщений для обёртки
        hist = list(chat_history) if chat_history is not None else [{"role": "user", "content": ""}]
        wrap_idx: set[int] = self._resolve_wrap_indices(hist, wrap_user)

        # 3) пройдём историю и «обернём» только выбранные user-сообщения
        user_tpl = templates.get("user")  # может отсутствовать
        for i, m in enumerate(hist):
            if m.get("role") == "user" and i in wrap_idx and user_tpl:
                # склеиваем vars + текст пользователя под ключом user_var
                extended = dict(vars)
                extended[user_var] = m.get("content", "")
                # для удобства — дубли под стандартными именами
                extended.setdefault("input", extended[user_var])
                extended.setdefault("user_content", extended[user_var])

                rendered = self._render(user_tpl, extended)
                messages.append({"role": "user", "content": rendered})
            else:
                # оставляем сообщение без изменений
                messages.append({"role": m["role"], "content": m["content"]})

        # 4) опциональные хвосты (assistant/tool) если нужны
        for tail_role in ("assistant", "tool"):
            if tail_role in templates:
                messages.append({"role": tail_role, "content": self._render(templates[tail_role], vars)})

        return messages

    def render_snippet(self, name: str, role: str, **vars) -> str:
        """Вернуть отрендеренный кусок конкретной роли (для превью/отладки)."""
        templates = self._load_templates(name)
        if role not in templates:
            raise FileNotFoundError(f"No '{role}.txt' for prompt '{name}'")
        return self._render(templates[role], vars)

    @classmethod
    def placeholders(cls, text: str) -> List[str]:
        """Вытащить список плейсхолдеров из текста шаблона."""
        return sorted({m.group("braced") or m.group("plain") for m in cls._ph_re.finditer(text)})

    # ---------- internals ----------
    def _load_templates(self, name: str) -> Dict[str, str]:
        folder = self.base_dir / name
        templates: Dict[str, str] = {}

        if folder.is_dir():
            for role in self._roles_order:
                p = folder / f"{role}.txt"
                if p.exists():
                    templates[role] = self._read_file(p)
            if templates:
                return templates

        # fallback: BASE_DIR/name.txt -> как system
        single = self.base_dir / f"{name}.txt"
        if single.exists():
            return {"system": self._read_file(single)}

        raise FileNotFoundError(f"Prompt '{name}' not found in '{folder}' or '{single}'")

    def _read_file(self, path: Path) -> str:
        mtime = path.stat().st_mtime
        cached = self._cache.get(path)
        if cached and cached[0] == mtime:
            return cached[1]
        text = path.read_text(encoding=self.encoding)
        self._cache[path] = (mtime, text)
        return text

    def _render(self, template: str, vars: Dict[str, str]) -> str:
        try:
            return Template(template).substitute(**vars)
        except KeyError as e:
            missing = str(e).strip("'")
            needed = ", ".join(self.placeholders(template)) or "(no vars)"
            raise ValueError(f"Missing placeholder '{missing}'. Required: {needed}")

    @staticmethod
    def _resolve_wrap_indices(
        hist: Sequence[Dict[str, str]],
        wrap_user: Union[str, int, Iterable[int], None],
    ) -> set[int]:
        """Определяет индексы user-сообщений, которые надо обернуть."""
        n = len(hist)
        user_indices = [i for i, m in enumerate(hist) if m.get("role") == "user"]

        def norm(i: int) -> int:
            return i if i >= 0 else n + i

        if wrap_user is None or wrap_user == "none":
            return set()
        if wrap_user == "all":
            return set(user_indices)
        if wrap_user == "last":
            return {user_indices[-1]} if user_indices else set()
        if isinstance(wrap_user, int):
            idx = norm(wrap_user)
            return {idx} if idx in user_indices else set()
        if isinstance(wrap_user, Iterable):
            res = set()
            for x in wrap_user:
                try:
                    idx = norm(int(x))
                    if idx in user_indices:
                        res.add(idx)
                except (TypeError, ValueError):
                    continue
            return res
        # по умолчанию — ничего
        return set()
