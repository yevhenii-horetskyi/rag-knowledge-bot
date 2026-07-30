-- ============================================================
--  RAG Knowledge Bot — налаштування бази в Supabase
--  Виконай це ОДИН РАЗ у Supabase → SQL Editor → New query → Run
-- ============================================================

-- 1) Увімкнути розширення pgvector (векторний пошук).
--    У Supabase воно вже є, просто активуємо.
create extension if not exists vector;

-- 2) Таблиця, де зберігаються шматки документів разом з їх embedding.
--    embedding vector(1536) — під модель text-embedding-3-small.
create table if not exists documents (
    id          bigserial primary key,
    content     text not null,           -- сам текст чанка
    source      text,                    -- назва файлу-джерела (для посилань)
    chunk_index int,                     -- номер чанка в документі
    embedding   vector(1536),            -- векторне представлення тексту
    created_at  timestamptz default now()
);

-- 3) Індекс для швидкого пошуку за косинусною близькістю.
create index if not exists documents_embedding_idx
    on documents using ivfflat (embedding vector_cosine_ops)
    with (lists = 100);

-- 4) Функція пошуку: приймає вектор питання, повертає найближчі чанки.
--    Викликається з Python через supabase.rpc('match_documents', {...}).
create or replace function match_documents (
    query_embedding vector(1536),
    match_count int default 5
)
returns table (
    id int,
    content text,
    source text,
    chunk_index int,
    similarity float
)
language sql stable
as $$
    select
        documents.id,
        documents.content,
        documents.source,
        documents.chunk_index,
        1 - (documents.embedding <=> query_embedding) as similarity
    from documents
    order by documents.embedding <=> query_embedding
    limit match_count;
$$;

-- Готово. Тепер база вміє зберігати документи й шукати по сенсу.
