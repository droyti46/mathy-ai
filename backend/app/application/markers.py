"""Utilities for aligning <w>...</w> markers with the original student text."""
from __future__ import annotations

import re
import unicodedata as _ud
from functools import lru_cache
from typing import List, Tuple

# =========================
#   ЛЕВЕНШТЕЙН (быстрый)
# =========================
try:  # pragma: no cover - optional dependency
    from rapidfuzz.distance import Levenshtein as _RFLev  # type: ignore

    def _lev(a: str, b: str) -> float:
        """Нормированное расстояние [0..1]."""
        if a == b:
            return 0.0
        d = _RFLev.distance(a, b)
        return d / max(len(a), len(b))

except Exception:  # pragma: no cover - fallback when rapidfuzz is absent
    import difflib as _difflib

    def _lev(a: str, b: str) -> float:
        """Запасной путь через difflib."""
        if a == b:
            return 0.0
        ratio = _difflib.SequenceMatcher(None, a, b).ratio()
        return 1.0 - ratio


# =========================================
#   ЭКВИВАЛЕНТНОСТИ СИМВОЛОВ / ПРОБЕЛОВ
# =========================================

_DEFAULT_CANDIDATE_MAPPING = {
    "\u00A0": " ",
    "\u2002": " ",
    "\u2003": " ",
    "\u2004": " ",
    "\u2005": " ",
    "\u2006": " ",
    "\u2007": " ",
    "\u2008": " ",
    "\u2009": " ",
    "\u200A": " ",
    "\u202F": " ",
    "\u205F": " ",
    "\u3000": " ",
    "\u200B": "",
    "\u200C": "",
    "\u200D": "",
    "\u2060": "",
    "\uFEFF": "",
    "\u2212": "-",
    "\u2010": "-",
    "\u2011": "-",
    "\u2012": "-",
    "\u2013": "-",
    "\u2014": "-",
    "\u2015": "-",
    "\u2043": "-",
    "\u2018": "'",
    "\u2019": "'",
    "\u201A": "'",
    "\u201B": "'",
    "\u201C": '"',
    "\u201D": '"',
    "\u201E": '"',
    "\u201F": '"',
    "\u00D7": "*",
    "\u22C5": "*",
    "\u2219": "*",
    "\u2215": "/",
    "\u2044": "/",
    "\u00F7": "/",
    "\u2217": "*",
    "\u27F6": "→",
    "\u2192": "→",
    "\u21D2": "⇒",
    "\u03BC": "μ",
    "\u00B5": "μ",
    "\u2264": "<=",
    "\u2265": ">=",
    "\u2260": "!=",
    "\u2261": "==",
    "\u221E": "∞",
}

_FORWARD_MAP: dict[str, str] | None = None
_EQUIV: dict[str, set[str]] | None = None
_WS_CLASS: str | None = None
_WS_RX: re.Pattern[str] | None = None


def _invert_mapping(candidate_mapping: dict[str, str]) -> dict[str, set[str]]:
    inv: dict[str, set[str]] = {}
    for src, dst in candidate_mapping.items():
        inv.setdefault(dst, set()).add(src)
    for dst in list(inv):
        inv[dst].add(dst)
    for base in [" ", "-", "'", '"', "*", "/", "→", "⇒", "μ", "<=", ">=", "!=", "==", "∞"]:
        inv.setdefault(base, set()).add(base)
    return inv


def _configure_equivalences(present_mapping: dict[str, str] | None = None) -> None:
    global _FORWARD_MAP, _EQUIV, _WS_CLASS, _WS_RX
    cm = present_mapping or _DEFAULT_CANDIDATE_MAPPING
    _FORWARD_MAP = cm.copy()
    _EQUIV = _invert_mapping(cm)

    ws_chars = set([" ", "\t"])
    ws_chars |= _EQUIV.get(" ", set()) if _EQUIV else set()
    cc = "".join(sorted({re.escape(c) for c in ws_chars}))
    _WS_CLASS = "[" + cc + "]"
    _WS_RX = re.compile(rf"(?:{_WS_CLASS}+)")

    try:
        _space_aware_rx.cache_clear()
    except Exception:  # pragma: no cover - cache invalidation best effort
        pass
    try:
        _best_fuzzy_span.cache_clear()
    except Exception:  # pragma: no cover
        pass


_configure_equivalences()


def _norm(s: str) -> str:
    if not isinstance(s, str):
        return ""
    out = _ud.normalize("NFKC", s)
    if _FORWARD_MAP:
        out = out.translate(str.maketrans(_FORWARD_MAP))
    out = out.replace("\r\n", "\n").replace("\r", "\n")
    if _WS_RX and _WS_CLASS:
        out = _WS_RX.sub(" ", out)
    else:  # pragma: no cover - fallback branch
        out = re.sub(r"[ \t\u00A0]+", " ", out)
    return out.casefold().strip()


def _extract_spans(generated_text: str) -> list[str]:
    """Достаёт внутренние тексты помеченных фрагментов из <w ...>...</w>."""
    gt = re.sub(r"</w>\s*<w\b[^>]*>", " ", generated_text)
    spans: list[str] = []
    for m in re.finditer(r"<w\b[^>]*>(.*?)</w>", gt, flags=re.DOTALL):
        inner = re.sub(r"</?w\b[^>]*>", "", m.group(1)).strip()
        if _norm(inner):
            spans.append(inner)
    return spans

def _extract_messages(generated_text: str) -> list[str]:
    """
    Возвращает список значений атрибута message из стартовых тегов <w ...> в порядке следования.
    Если у тега нет message, в список добавляется пустая строка.
    """
    gt = re.sub(r"</w>\s*<w\b[^>]*>", " ", generated_text)
    msgs: list[str] = []
    for m in re.finditer(r"<w\b([^>]*)>", gt, flags=re.DOTALL):
        attrs = m.group(1) or ""
        mm = re.search(r'\bmessage=(?:"([^"]*)"|\'([^\']*)\')', attrs, flags=re.DOTALL)
        if mm:
            val = mm.group(1) if mm.group(1) is not None else mm.group(2) or ""
            msgs.append(val.strip())
        else:
            msgs.append("")
    return msgs


_LATEX_TO_UNI = {
    "sum": "∑",
    "prod": "∏",
    "sigma": "σ",
    "Sigma": "Σ",
    "tau": "τ",
    "Tau": "Τ",
    "in": "∈",
}

_SPACING_MACROS = {",", ";", ":", " ", "!"}


def _space_and_equiv_aware_pattern(pat: str) -> str:
    out: list[str] = []
    i = 0
    multi_tokens: list[str] = []
    if _EQUIV:
        multi_tokens = sorted([t for t in _EQUIV.keys() if len(t) > 1], key=len, reverse=True)

    N = len(pat)
    while i < N:
        if _WS_RX and _WS_CLASS:
            m = _WS_RX.match(pat, i)
        else:  # pragma: no cover - backup branch
            m = re.match(r"[ \t\u00A0]+", pat[i:])
            if m:
                out.append(r"(?:[ \t\u00A0]+)")
                i += m.end()
                continue
        if m:
            out.append(rf"(?:{_WS_CLASS}+)")
            i = m.end()
            continue

        ch = pat[i]
        if ch == "$":
            i += 1
            continue

        matched_multi = False
        for tok in multi_tokens:
            if pat.startswith(tok, i):
                alts = sorted(_EQUIV.get(tok, {tok}), key=len, reverse=True) if _EQUIV else [tok]
                out.append("(?:%s)" % "|".join(re.escape(a) for a in alts))
                i += len(tok)
                matched_multi = True
                break
        if matched_multi:
            continue

        if ch == "\\" and i + 1 < N:
            nxt = pat[i + 1]
            if nxt.isalpha():
                j = i + 2
                while j < N and pat[j].isalpha():
                    j += 1
                name = pat[i + 1 : j]
                if name in _LATEX_TO_UNI:
                    uni = _LATEX_TO_UNI[name]
                    out.append("(?:%s|%s)" % (re.escape("\\" + name), re.escape(uni)))
                    i = j
                    continue
                out.append(re.escape("\\" + name))
                i = j
                continue
            if nxt in _SPACING_MACROS:
                literal = "\\" + nxt
                if nxt == "!":
                    out.append("(?:%s|)" % re.escape(literal))
                else:
                    if _WS_CLASS:
                        out.append("(?:%s|%s+)" % (re.escape(literal), _WS_CLASS))
                    else:
                        out.append(re.escape(literal))
                i += 2
                continue
            out.append(re.escape("\\" + nxt))
            i += 2
            continue

        if _EQUIV and ch in _EQUIV:
            eq = _EQUIV[ch]
            single = [c for c in eq if len(c) == 1]
            multi = [c for c in eq if len(c) > 1]
            parts: list[str] = []
            if single:
                parts.append("[" + "".join(sorted({re.escape(c) for c in single})) + "]")
            parts += [re.escape(c) for c in sorted(multi, key=len, reverse=True)]
            out.append(parts[0] if len(parts) == 1 else "(?:%s)" % "|".join(parts))
            i += 1
            continue

        out.append(re.escape(ch))
        i += 1

    return "".join(out) or r"(?:)"


def _is_short_alnum_token(pat: str) -> bool:
    s = _norm(pat)
    return 1 <= len(s) <= 2 and s.isalnum()


def _is_word_char(ch: str) -> bool:
    return bool(ch) and (ch.isalnum() or ch == "_")


def _inside_word(text: str, s: int, e: int) -> bool:
    left = text[s - 1] if s > 0 else ""
    right = text[e] if e < len(text) else ""
    return _is_word_char(left) and _is_word_char(right)


@lru_cache(maxsize=4096)
def _space_aware_rx(pat: str) -> re.Pattern[str]:
    core = _space_and_equiv_aware_pattern(pat)
    if _is_short_alnum_token(pat):
        core = r"(?<!\w)" + core + r"(?!\w)"
    return re.compile(core, flags=re.DOTALL)


def _space_aware_search(text: str, start_pos: int, pattern: str) -> tuple[int, int] | None:
    if not pattern:
        return None
    m = _space_aware_rx(pattern).search(text, start_pos)
    return (m.start(), m.end()) if m else None


def _anchor_candidates(region: str, pat: str, max_hits: int = 60) -> list[int]:
    pat_head = pat[:14]
    anchors: list[str] = []
    if len(pat_head) >= 3:
        anchors.append(pat_head)
    m = re.search(r"[A-Za-zА-Яа-я0-9]{4,}", pat)
    if m:
        anchors.append(m.group(0))
    m2 = re.search(r"[\(\)\[\]\{\}\^\+\-\=\/\\\|\*]{2,}", pat)
    if m2:
        anchors.append(m2.group(0))

    starts: set[int] = set()
    for a in anchors:
        rx = _space_aware_rx(a)
        for hit in rx.finditer(region):
            starts.add(hit.start())
            if len(starts) >= max_hits:
                break
        if len(starts) >= max_hits:
            break

    if not starts:
        starts.add(0)

    more: list[int] = []
    for s in list(starts):
        if _WS_CLASS:
            m3 = re.search(rf"(?<={_WS_CLASS})\S", region[s:])
        else:
            m3 = re.search(r"(?<=[ \t])\S", region[s:])
        if m3:
            more.append(s + m3.start())
    starts.update(more)

    return sorted(starts)[:max_hits]


def _max_acceptable_score(L: int) -> float:
    if L <= 4:
        return 0.0
    if L <= 7:
        return 0.06
    if L <= 12:
        return 0.12
    return 0.18


@lru_cache(maxsize=4096)
def _best_fuzzy_span(text: str, start_pos: int, pattern: str, *, window: int = 280):
    def _is_short_alnum_token_local(pat: str) -> bool:
        s = _norm(pat)
        return 1 <= len(s) <= 2 and s.isalnum()

    def _is_word_char_local(ch: str) -> bool:
        return bool(ch) and (ch.isalnum() or ch == "_")

    def _inside_word_local(txt: str, s: int, e: int) -> bool:
        left = txt[s - 1] if s > 0 else ""
        right = txt[e] if e < len(txt) else ""
        return _is_word_char_local(left) and _is_word_char_local(right)

    short_token = _is_short_alnum_token_local(pattern)

    pat_n = _norm(pattern)
    if not pat_n:
        return None

    idx = text.find(pattern, start_pos)
    if idx != -1 and not (short_token and _inside_word_local(text, idx, idx + len(pattern))):
        return {"start": idx, "end": idx + len(pattern), "score": 0.0}

    rx = _space_aware_rx(pattern)
    m = rx.search(text, start_pos)
    while m and short_token and _inside_word_local(text, m.start(), m.end()):
        m = rx.search(text, m.end())
    if m:
        return {"start": m.start(), "end": m.end(), "score": 0.0}

    reg_len = max(window, int(3.5 * len(pat_n) + 40))
    region = text[start_pos : start_pos + reg_len]
    if not region:
        return None

    idx2 = region.find(pattern)
    if idx2 != -1:
        s = start_pos + idx2
        if not (short_token and _inside_word_local(text, s, s + len(pattern))):
            return {"start": s, "end": s + len(pattern), "score": 0.0}

    m = rx.search(region)
    while m and short_token and _inside_word_local(text, start_pos + m.start(), start_pos + m.end()):
        m = rx.search(region, m.end())
    if m:
        s = start_pos + m.start()
        e = start_pos + m.end()
        return {"start": s, "end": e, "score": 0.0}

    starts = _anchor_candidates(region, pattern, max_hits=60) or [0]
    L = max(1, len(pat_n))
    lengths = sorted({L, max(1, int(L * 0.85)), int(L * 1.2)})
    best = None
    best_score = 1e9
    accept = _max_acceptable_score(L)

    for i in starts:
        for ell in lengths:
            cand = region[i : i + ell]
            if not cand:
                continue
            s_abs = start_pos + i
            e_abs = s_abs + len(cand)
            if short_token and _inside_word_local(text, s_abs, e_abs):
                continue
            score = _lev(_norm(cand), pat_n)
            if score < best_score - 1e-6 or (
                abs(score - best_score) < 1e-6 and s_abs < (best["start"] if best else 10**9)
            ):
                best_score = score
                best = {"start": s_abs, "end": e_abs, "score": score}
                if score == 0.0:
                    return best
        if best and best["score"] <= min(0.05, accept):
            return best

    if not best or best["score"] > accept:
        return None
    return best


def stitch_markers_fast(original_text: str, generated_text: str, neighbor_margin: float = 0.12) -> str:
    gen_spans = _extract_spans(generated_text)
    gen_msgs = _extract_messages(generated_text)
    if not gen_spans:
        return original_text

    out: list[str] = []
    pos = 0
    i = 0
    n = len(gen_spans)
    while i < n:
        g = gen_spans[i]
        best_g = _best_fuzzy_span(original_text, pos, g)
        best_next = (
            _best_fuzzy_span(original_text, pos, gen_spans[i + 1]) if i + 1 < n else None
        )

        if (
            best_g
            and best_next
            and (best_next["score"] + neighbor_margin < best_g["score"])
            and (best_next["start"] <= best_g["start"])
        ):
            out.append(original_text[pos : best_next["start"]])
            pos = best_next["start"]
            best_g = _best_fuzzy_span(original_text, pos, g)

        if not best_g:
            i += 1
            continue

        s, e = best_g["start"], best_g["end"]
        if s > pos:
            out.append(original_text[pos:s])

        def _esc_attr(v: str) -> str:
            return (
                v.replace("&", "&amp;")
                 .replace('"', "&quot;")
                 .replace("<", "&lt;")
                 .replace(">", "&gt;")
            )

        attr = ""
        if i < len(gen_msgs) and gen_msgs[i]:
            attr = f' message="{_esc_attr(gen_msgs[i])}"'

        out.append(f"<w{attr}>" + original_text[s:e] + "</w>")
        pos = e
        i += 1

    out.append(original_text[pos:])
    return "".join(out)

def extract_tag_segments(text: str) -> List[List[int]]:
    segments: List[List[int]] = []
    plain_pos = 0
    # Поддерживаем стартовые теги с атрибутами: <w ...>
    token_pattern = re.compile(r"<w\b[^>]*>|</w>|[^<]+|<")

    active = False
    start_pos: int | None = None

    for m in token_pattern.finditer(text):
        token = m.group(0)
        if token.startswith("<w"):
            active = True
            start_pos = plain_pos
        elif token == "</w>":
            if active and start_pos is not None and plain_pos > start_pos:
                segments.append([start_pos, plain_pos])
            active = False
            start_pos = None
        else:
            plain_pos += len(token)

    if active and start_pos is not None and plain_pos > start_pos:
        segments.append([start_pos, plain_pos])

    return segments


_COT_BLOCK_RX = re.compile(r"<think>.*?</think>", re.IGNORECASE | re.DOTALL)
_CODE_FENCE_THINK_RX = re.compile(r"```think.*?```", re.IGNORECASE | re.DOTALL)
_THINK_PREFIX_RX = re.compile(r"(?is)\A\s*(?:think\s*[:：]|<think>)")


def extract_marked_solution(raw_text: str) -> str:
    if not raw_text:
        return ""
    text = _COT_BLOCK_RX.sub("", raw_text)
    text = _CODE_FENCE_THINK_RX.sub("", text)
    idx = text.rfind("</think>")
    if idx != -1:
        text = text[idx + len("</think>") :]
    text = text.strip()
    if _THINK_PREFIX_RX.match(text):
        text = _THINK_PREFIX_RX.sub("", text).lstrip("-:> ")
    if text.lower().startswith("answer:"):
        text = text[len("answer:") :]
    return text.strip()


def postprocess_marked_text(original: str, raw_marked: str) -> Tuple[str, List[List[int]], List[str]]:
    """
    Возвращает:
      - stitched: исходный текст с пришитыми <w message="...">...</w>
      - segments: [[start, end], ...] в координатах plain-текста
      - messages: список сообщений по порядку тегов
    """
    cleaned = extract_marked_solution(raw_marked)
    stitched = stitch_markers_fast(original, cleaned)
    segments = extract_tag_segments(stitched)
    messages = _extract_messages(cleaned)
    return stitched, segments, messages

