# RAG Knowledge Bot

A Telegram bot that answers questions over uploaded documents. Send a PDF or text
file — the bot indexes it into a vector database and answers questions grounded
only in those documents, with a reference to the source.

**Stack:** Python · OpenAI (embeddings + LLM) · Supabase (PostgreSQL + pgvector) · python-telegram-bot

---

## What it is and how it works

The bot uses **RAG (Retrieval-Augmented Generation)** — it answers based on real
documents rather than the model's own memory:

1. each document is split into chunks, each chunk is turned into a vector (embedding) and stored in the database;
2. when a question comes in, it is also turned into a vector, and the most semantically similar chunks are retrieved from the database;
3. the retrieved chunks are passed to the model as context, and it produces an answer based only on them.

This keeps answers grounded in real data instead of guesses, and every answer has
a source. Vector storage and search are handled by the **pgvector** extension in
PostgreSQL (Supabase).

---

## Architecture

```
Document ──► split into chunks ──► embeddings (OpenAI) ──► Supabase (pgvector)

Question ──► embedding ──► pgvector search ──► most relevant chunks
                                                      │
                                                      ▼
                            LLM (answers from context only) ──► answer + source
```

```
src/
├── config.py    # keys and parameters (model, chunk size)
├── ingest.py    # file → chunks → embeddings → database
├── rag.py       # retrieve chunks + generate the answer
└── bot.py       # Telegram bot
setup.sql        # pgvector table + search function (run in Supabase)
```

---

## Setup

**1. Supabase.** Create a free project at supabase.com → SQL Editor →
paste the contents of `setup.sql` → Run.

**2. Keys.** Copy `.env.example` to `.env` and fill in:
- `OPENAI_API_KEY`
- `SUPABASE_URL` and `SUPABASE_KEY` (Settings → API, service_role key)
- `TELEGRAM_BOT_TOKEN` (from @BotFather)

**3. Install and run.**
```bash
python -m venv venv && source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
python -m src.bot
```

**4. Usage.** Open the bot in Telegram → send a PDF/txt → ask a question.
