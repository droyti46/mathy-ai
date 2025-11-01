from dataclasses import dataclass

@dataclass
class Task:
    id: str
    theme_id: str
    name: str
    difficulty: str
    statement_md: str
    reference_solution_md: str | None = None
    source: str | None = None
    tags: list[str] = None
