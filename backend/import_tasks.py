import argparse
import pandas as pd
import re
import unicodedata
from pathlib import Path

def slugify(value: str) -> str:
    value = str(value).strip().lower()
    tr = {
        'а':'a','б':'b','в':'v','г':'g','д':'d','е':'e','ё':'e','ж':'zh','з':'z','и':'i','й':'i',
        'к':'k','л':'l','м':'m','н':'n','о':'o','п':'p','р':'r','с':'s','т':'t','у':'u','ф':'f',
        'х':'h','ц':'c','ч':'ch','ш':'sh','щ':'sch','ъ':'','ы':'y','ь':'','э':'e','ю':'yu','я':'ya'
    }
    value = ''.join(tr.get(ch, ch) for ch in value)
    value = unicodedata.normalize('NFKD', value)
    value = re.sub(r'[^a-z0-9]+', '-', value)
    value = re.sub(r'-{2,}', '-', value).strip('-')
    return value or "theme"

DIFF_MAP = {
    'легкий':'easy', 'лёгкий':'easy', 'easy':'easy', 'простой':'easy',
    'средний':'medium', 'medium':'medium', 'нормальный':'medium',
    'сложный':'hard', 'тяжелый':'hard', 'тяжёлый':'hard', 'hard':'hard'
}

def map_difficulty(x: str) -> str:
    if x is None:
        return 'easy'
    s = str(x).strip().lower()
    return DIFF_MAP.get(s, 'medium')

def run(input_path: Path, output_path: Path, start_id: int = 1):
    df = pd.read_csv(input_path)
    cols = {c.lower().strip(): c for c in df.columns}

    def pick(*names):
        for n in names:
            key = n.lower().strip()
            if key in cols:
                return cols[key]
        raise KeyError(f"Missing column among: {names}")

    col_task = pick("task", "текст", "условие")
    col_theme = pick("тема", "theme")
    col_diff = pick("уровень сложности", "difficulty", "сложность")
    col_sol  = pick("решение", "solution", "reference_solution")

    out = []
    for i, row in df.iterrows():
        statement = str(row.get(col_task, "")).strip()
        theme_raw = str(row.get(col_theme, "math")).strip() or "math"
        theme_id = slugify(theme_raw)
        difficulty = map_difficulty(row.get(col_diff, ""))
        solution = str(row.get(col_sol, "")).strip()
        out.append({
            "id": str(start_id + i),
            "theme_id": theme_id,
            "difficulty": difficulty,
            "statement_md": statement,
            "reference_solution_md": solution,
            "source": "user-dataset",
            "tags": ""
        })

    out_df = pd.DataFrame(out, columns=[
        "id","theme_id","difficulty","statement_md","reference_solution_md","source","tags"
    ])
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if output_path.suffix.lower() == ".parquet":
        out_df.to_parquet(output_path, index=False)
    else:
        out_df.to_csv(output_path, index=False, encoding="utf-8")
    print(f"Wrote {len(out_df)} rows -> {output_path}")

if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Import dataset (task, тема, уровень сложности, решение) into data/tasks.csv")
    ap.add_argument("--input", required=True, help="Path to your CSV")
    ap.add_argument("--output", default="data/tasks.csv", help="Where to write (CSV or Parquet). Default: data/tasks.csv")
    ap.add_argument("--start-id", type=int, default=1, help="First numeric id to assign")
    args = ap.parse_args()
    run(Path(args.input), Path(args.output), start_id=args.start_id)
