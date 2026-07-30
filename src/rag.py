"""Пошук релевантних чанків і генерація відповіді з джерелами.

Це «R» і «G» у RAG:
  Retrieval — знайти в базі шматки, найближчі за сенсом до питання.
  Generation — дати їх LLM як контекст і попросити відповісти ТІЛЬКИ по них.
"""
from openai import OpenAI
from supabase import create_client

from .config import (
    OPENAI_API_KEY, SUPABASE_URL, SUPABASE_KEY,
    EMBEDDING_MODEL, ANSWER_MODEL, TOP_K,
)

openai_client = OpenAI(api_key=OPENAI_API_KEY)
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


def retrieve(question: str, top_k: int = TOP_K) -> list[dict]:
    """Знайти top_k найрелевантніших чанків під питання.

    1) перетворюємо питання на вектор тією ж моделлю, що й документи;
    2) кличемо функцію match_documents у Supabase — вона порівнює вектори.
    """
    q_vec = openai_client.embeddings.create(
        model=EMBEDDING_MODEL, input=[question]
    ).data[0].embedding

    resp = supabase.rpc(
        "match_documents",
        {"query_embedding": q_vec, "match_count": top_k},
    ).execute()
    return resp.data or []


def answer(question: str) -> dict:
    """Повна RAG-відповідь: retrieve → побудувати контекст → LLM.

    Ключова ідея: модель відповідає ЛИШЕ на основі знайдених чанків.
    Якщо у контексті відповіді нема — чесно каже про це, а не вигадує.
    """
    chunks = retrieve(question)
    if not chunks:
        return {"answer": "У базі немає документів або нічого релевантного не знайдено.", "sources": []}

    # Збираємо контекст із пронумерованих джерел, щоб на них можна було послатись.
    context = "\n\n".join(
        f"[{i + 1}] (джерело: {c['source']})\n{c['content']}"
        for i, c in enumerate(chunks)
    )

    system = (
        "Ти асистент, який відповідає ТІЛЬКИ на основі наданого контексту. "
        "Якщо відповіді в контексті немає — скажи про це прямо, не вигадуй. "
        "У кінці відповіді вкажи номери джерел у форматі [1], [2], на які спирався."
    )
    user = f"Контекст:\n{context}\n\nПитання: {question}"

    resp = openai_client.chat.completions.create(
        model=ANSWER_MODEL,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        temperature=0.2,
    )

    # Унікальні джерела для показу користувачу
    sources = []
    seen = set()
    for c in chunks:
        if c["source"] not in seen:
            seen.add(c["source"])
            sources.append(c["source"])

    return {"answer": resp.choices[0].message.content, "sources": sources}


if __name__ == "__main__":
    import sys
    q = " ".join(sys.argv[1:]) or "Про що ці документи?"
    result = answer(q)
    print(result["answer"])
    print("\nДжерела:", ", ".join(result["sources"]))
