"""Налаштування RAG-бота. Усі ключі — зі змінних середовища (.env)."""
import os

# OpenAI — для embeddings і генерації відповіді
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

# Supabase — база з pgvector (Project URL + service_role ключ з Settings → API)
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

# Telegram — токен бота від @BotFather
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")

# ---- Параметри RAG ----
# Модель embeddings: text-embedding-3-small дає 1536 вимірів, дешева й точна.
EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_DIM = 1536

# Модель для відповіді
ANSWER_MODEL = "gpt-4o-mini"

# Розбивка документів на чанки (у словах). overlap — щоб не різати думку навпіл.
CHUNK_WORDS = 350
CHUNK_OVERLAP = 60

# Скільки найрелевантніших чанків підтягувати під питання
TOP_K = 5
