import uuid
from pathlib import Path

class LocalStorage:
    def __init__(self, base_dir: str = "var/storage"):
        self.base = Path(base_dir)
        self.base.mkdir(parents=True, exist_ok=True)

    async def save(self, file_bytes: bytes, ext: str) -> str:
        name = f"{uuid.uuid4().hex}.{ext}".strip(".")
        path = self.base / name
        with open(path, "wb") as f:
            f.write(file_bytes)
        return str(path)
