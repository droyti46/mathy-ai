# app/infrastructure/ocr/vision_openrouter.py
from __future__ import annotations
import base64, io, os
from typing import Optional, List
import httpx
from fastapi import UploadFile, HTTPException
from PIL import Image

try:
    import fitz  # PyMuPDF
    HAS_FITZ = True
except Exception:
    HAS_FITZ = False

class VisionOCROpenRouter:
    def __init__(
        self,
        model: Optional[str] = None,
        api_key: Optional[str] = None,
        base_url: str = "https://openrouter.ai/api/v1",
        trust_env: bool = True,
    ):
        self.model = model or "google/gemini-2.5-flash"
        self.api_key = api_key or ""
        self.base_url = base_url.rstrip("/")
        self.trust_env = trust_env

        # подготовим клиент с ретраями/лимитами (можно переиспользовать, если вынесешь в контейнер)
        self._transport = httpx.AsyncHTTPTransport(retries=2)
        self._limits = httpx.Limits(max_keepalive_connections=5, max_connections=10)

    async def extract_text(self, file: UploadFile) -> str:
        if not self.api_key:
            raise HTTPException(status_code=500, detail="OPENROUTER_API_KEY не задан")

        content_type = (file.content_type or "").lower()
        filename = file.filename or ""
        raw = await file.read()

        if content_type.startswith("text/") or self._is_text_extension(filename):
            return self._decode_text(raw, content_type or filename)

        if content_type.startswith("image/"):
            return await self._ocr_image_bytes(raw, mime=content_type)

        if content_type == "application/pdf":
            if not HAS_FITZ:
                raise HTTPException(
                    status_code=415,
                    detail="Для PDF нужен PyMuPDF (pymupdf). Установи пакет и повтори запрос."
                )
            return await self._ocr_pdf_bytes(raw)

        # Пустой/левый content-type: пробуем как картинку
        try:
            Image.open(io.BytesIO(raw))
            return await self._ocr_image_bytes(raw, mime="image/png")
        except Exception:
            raise HTTPException(status_code=415, detail=f"Неподдерживаемый тип файла: {content_type or 'unknown'}")

    async def _ocr_pdf_bytes(self, pdf_bytes: bytes, max_pages: int = 10, dpi: int = 200) -> str:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        texts: List[str] = []
        try:
            pages = min(len(doc), max_pages)
            for i in range(pages):
                page = doc.load_page(i)
                mat = fitz.Matrix(dpi / 72, dpi / 72)
                pix = page.get_pixmap(matrix=mat, alpha=False)
                img_bytes = pix.tobytes("png")
                t = await self._ocr_image_bytes(img_bytes, mime="image/png", page_num=i + 1)
                if t:
                    texts.append(t.strip())
        finally:
            doc.close()
        return "\n\n--- PAGE BREAK ---\n\n".join([t for t in texts if t])

    async def _ocr_image_bytes(self, image_bytes: bytes, mime: str = "image/png", page_num: Optional[int] = None) -> str:
        data_url = self._to_data_url(image_bytes, mime)
        user_text = (
            "Тебе дано изображение страницы решения. Распознай изображение 1:1 и верни ровно один цельный фрагмент русского текста"
            "без LaTeX, без Markdown и без любой другой разметки.\n"
            "Пиши только то, что напечатано в решении. Не добавляй пояснений, не перефразируй. Но пиши по-русски: явные опечатки в словах исправляй.\n"
            "Правила формата:\n"
            "1) Ничего лишнего нельзя добавлять или что-то лишнее убирать ни в коем случае и ни при каких обстоятельствах. Слово в слово, только с математикой есть нюансы. Не продолжай рассуждения автора, даже если видно, что они пропущены, только переписывай текст с картинки.\n"
            "2) Не заменяй слова на символы и наоборот. Например, если написано «x стремится к нулю», так и пиши; если написано «x→0», пиши «x→0» Если написано 'плюс', пиши 'плюс', если '+' - пиши '+'.\n"
            "3) Сохраняй порядок изложения и абзацы как на странице; не переставляй части и не сокращай ход рассуждений. Но если какая-то часть текста зачёркнута, не пиши её.\n"
            "4) Степени писать вот так, если один символ (например): x^2, x^a и вот так, если несколько (например): x^{3/2}, 3^{200}.\n"
            "5) Аналогично с корнями: ∛5 (скобки нет, так как символ под знаком корня один),√(-10); аналогично с индексами: x_1, a_{k1}, a_{k1}x_1.\n"
            "6) И точно также с другими функциями: ∫_{x0}^x, ∫_0^π, lim_{x→0}.\n"
            "Ещё примеры правильной записи: С_{20}^2 (а не C(20, 2)), f_n'(t), |sin y|,  (sin x)/x, ∑_{k=1}^n k^2 = n(n+1)(2n+1), (a+b)/(c+d), log_2 x.\n"
        )

        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": user_text},
                        {"type": "image_url", "image_url": {"url": data_url}},
                    ],
                },
            ],
            "temperature": 0.0,
        }

        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "HTTP-Referer": "https://example.com",
            "X-Title": "Math Trainer OCR",
            "Content-Type": "application/json",
        }

        try:
            async with httpx.AsyncClient(
                timeout=120,
                base_url=self.base_url,          # единый base_url как у LLMRouter
                transport=self._transport,
                limits=self._limits,
                trust_env=self.trust_env,        # совпадает с окружением (proxy и т.п.)
                http2=True,                      # обычно у OpenRouter всё ок с h2
            ) as client:
                resp = await client.post(
                    "/chat/completions",  # используем относительный путь
                    headers=headers,
                    json=payload,
                )
        except httpx.HTTPError as exc:
            # вернём тип и сообщение, чтобы понять первопричину (DNS/SSL/proxy)
            raise HTTPException(status_code=502, detail=f"OCR connect error: {type(exc).__name__}: {exc}") from exc

        if resp.status_code >= 400:
            raise HTTPException(status_code=502, detail=f"OCR upstream error: {resp.status_code} {resp.text}")

        data = resp.json()
        try:
            text = data["choices"]["0"]["message"]["content"]  # иногда приходит с ключом-строкой
        except Exception:
            try:
                text = data["choices"][0]["message"]["content"]
            except Exception:
                raise HTTPException(status_code=502, detail=f"OCR bad response: {data}")

        return (text or "").strip()

    @staticmethod
    def _to_data_url(b: bytes, mime: str) -> str:
        return f"data:{mime};base64," + base64.b64encode(b).decode("ascii")

    @staticmethod
    def _is_text_extension(filename: str) -> bool:
        _, ext = os.path.splitext(filename.lower())
        return ext in {".txt", ".md", ".markdown", ".text"}

    @staticmethod
    def _decode_text(raw: bytes, source: str) -> str:
        try:
            return raw.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise HTTPException(status_code=415, detail=f"Не удалось прочитать текстовый файл ({source}). Ожидается UTF-8") from exc
