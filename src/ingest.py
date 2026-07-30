"""Завантаження документів у базу (ingestion).

Потік:  файл → текст → чанки → embeddings → Supabase.
Це «індексація» — робиться один раз на кожен документ. Після цього
бот може відповідати на питання по ньому.
"""
from pathlib import Path

from openai import OpenAI
from supabase import create_client

from .config import (
    OPENAI_API_KEY, SUPABASE_URL, SUPABASE_KEY,
    EMBEDDING_MODEL, CHUNK_WORDS, CHUNK_OVERLAP,
)

openai_client = OpenAI(api_key=OPENAI_API_KEY)
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


def read_file(path: Path) -> str:
    """Витягнути текст із файлу. Підтримка .txt, .md, .pdf."""
    suffix = path.suffix.lower()
    if suffix in (".txt", ".md"):
        return path.read_text(encoding="utf-8", errors="ignore")
    if suffix == ".pdf":
        from pypdf import PdfReader
        reader = PdfReader(str(path))
        return "\n".join((page.extract_text() or "") for page in reader.pages)
    raise ValueError(f"Непідтримуваний формат: {suffix}")


def chunk_text(text: str) -> list[str]:
    """Порізати текст на чанки по ~CHUNK_WORDS слів з перекриттям CHUNK_OVERLAP.

    Перекриття потрібне, щоб думка на межі чанків не губилась — інакше
    відповідь може «розірватись» між двома шматками.
    """
    words = text.split()
    if not words:
        return []
    chunks, start = [], 0
    step = CHUNK_WORDS - CHUNK_OVERLAP
    while start < len(words):
        chunk = " ".join(words[start:start + CHUNK_WORDS])
        chunks.append(chunk)
        start += step
    return chunks


def embed(texts: list[str]) -> list[list[float]]:
    """Перетворити список текстів на вектори через OpenAI."""
    resp = openai_client.embeddings.create(model=EMBEDDING_MODEL, input=texts)
    return [d.embedding for d in resp.data]


def ingest_file(path: Path) -> int:
    """Проіндексувати один файл. Повертає кількість збережених чанків."""
    text = read_file(path)
    chunks = chunk_text(text)
    if not chunks:
        return 0

    vectors = embed(chunks)
    rows = [
        {"content": c, "source": path.name, "chunk_index": i, "embedding": v}
        for i, (c, v) in enumerate(zip(chunks, vectors))
    ]
    supabase.table("documents").insert(rows).execute()
    return len(rows)


def ingest_folder(folder: str = "docs") -> dict:
    """Проіндексувати всі підтримувані файли з папки."""
    result = {}
    for path in Path(folder).glob("*"):
        if path.suffix.lower() in (".txt", ".md", ".pdf"):
            try:
                result[path.name] = ingest_file(path)
            except Exception as e:
                result[path.name] = f"помилка: {e}"
    return result


if __name__ == "__main__":
    # Запуск вручну: python -m src.ingest  → проіндексує все з папки docs/
    print("Індексую папку docs/ …")
    for name, count in ingest_folder().items():
        print(f"  {name}: {count} чанків")
