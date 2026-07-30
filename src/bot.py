"""Telegram-бот: обличчя RAG-системи.

Що вміє:
  /start           — привітання
  надіслати файл   — бот індексує його (додає в базу знань)
  надіслати питання — бот відповідає по завантажених документах із джерелами
"""
import tempfile
from pathlib import Path

from telegram import Update
from telegram.ext import (
    Application, CommandHandler, MessageHandler, ContextTypes, filters,
)

from .config import TELEGRAM_BOT_TOKEN
from .ingest import ingest_file
from .rag import answer

WELCOME = (
    "👋 Привіт! Я RAG-бот бази знань.\n\n"
    "• Надішли мені документ (.pdf, .txt, .md) — я додам його в базу.\n"
    "• Потім став будь-яке питання — відповім по твоїх документах і вкажу джерело.\n\n"
    "Спробуй завантажити файл і запитати щось по ньому."
)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(WELCOME)


async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Користувач надіслав файл → качаємо → індексуємо."""
    doc = update.message.document
    if not Path(doc.file_name).suffix.lower() in (".pdf", ".txt", ".md"):
        await update.message.reply_text("Підтримую тільки .pdf, .txt, .md")
        return

    await update.message.reply_text(f"📥 Індексую «{doc.file_name}»…")
    tg_file = await doc.get_file()

    with tempfile.TemporaryDirectory() as tmp:
        local = Path(tmp) / doc.file_name
        await tg_file.download_to_drive(str(local))
        try:
            n = ingest_file(local)
            await update.message.reply_text(f"✅ Готово: {n} фрагментів додано в базу. Можеш ставити питання.")
        except Exception as e:
            await update.message.reply_text(f"⚠️ Помилка індексації: {e}")


async def handle_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Звичайне текстове повідомлення → RAG-відповідь."""
    question = update.message.text.strip()
    if not question:
        return
    await update.message.chat.send_action("typing")
    try:
        result = answer(question)
        text = result["answer"]
        if result["sources"]:
            text += "\n\n📎 Джерела: " + ", ".join(result["sources"])
        await update.message.reply_text(text)
    except Exception as e:
        await update.message.reply_text(f"⚠️ Помилка: {e}")


def main():
    if not TELEGRAM_BOT_TOKEN:
        raise SystemExit("Немає TELEGRAM_BOT_TOKEN у .env")

    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_question))

    print("Бот запущено. Відкрий його в Telegram.")
    app.run_polling()


if __name__ == "__main__":
    main()
