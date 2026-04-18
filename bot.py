import os
from datetime import datetime

import requests
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
TRELLO_KEY = os.getenv("TRELLO_KEY")
TRELLO_TOKEN = os.getenv("TRELLO_TOKEN")
TRELLO_LIST_ID = os.getenv("TRELLO_LIST_ID")


def build_card_title(text: str, max_length: int = 80) -> str:
    text = " ".join(text.strip().split())

    first_sentence = text.split(".", 1)[0].strip()
    if not first_sentence:
        first_sentence = text

    if len(first_sentence) <= max_length:
        return first_sentence

    return first_sentence[: max_length - 3].rstrip() + "..."


def build_card_description(task_text: str, author_name: str) -> str:
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    return (
        f"Имя: {author_name}\n"
        f"Время: {created_at}\n\n"
        "Текст:\n"
        f"{task_text}"
    )


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Бот жив. Ответь командой /Vlad на сообщение, и я создам карточку в Trello."
    )


async def vlad(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message

    if not message:
        return

    if not message.reply_to_message:
        await context.bot.send_message(chat_id=message.chat_id, text="Не получилось")
        return

    original_message = message.reply_to_message

    if not original_message.text:
        await context.bot.send_message(chat_id=message.chat_id, text="Не получилось")
        return

    task_text = original_message.text.strip()
    if not task_text:
        await context.bot.send_message(chat_id=message.chat_id, text="Не получилось")
        return

    author = original_message.from_user
    author_name = author.full_name if author else "Неизвестно"

    card_name = build_card_title(task_text)
    card_desc = build_card_description(task_text, author_name)

    url = "https://api.trello.com/1/cards"
    params = {
        "idList": TRELLO_LIST_ID,
        "name": card_name,
        "desc": card_desc,
        "key": TRELLO_KEY,
        "token": TRELLO_TOKEN,
    }

    try:
        response = requests.post(url, params=params, timeout=15)
        response.raise_for_status()
    except requests.RequestException:
        await context.bot.send_message(chat_id=message.chat_id, text="Не получилось")
        return

    card = response.json()
    card_url = card.get("url", "")

    if card_url:
        await context.bot.send_message(
            chat_id=message.chat_id,
            text=f"Финализировал. {card_url}"
        )
    else:
        await context.bot.send_message(chat_id=message.chat_id, text="Не получилось")

def main():
    required_vars = {
        "BOT_TOKEN": BOT_TOKEN,
        "TRELLO_KEY": TRELLO_KEY,
        "TRELLO_TOKEN": TRELLO_TOKEN,
        "TRELLO_LIST_ID": TRELLO_LIST_ID,
    }

    missing_vars = [name for name, value in required_vars.items() if not value]
    if missing_vars:
        raise ValueError(
            "Не найдены переменные окружения: " + ", ".join(missing_vars)
        )

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("Vlad", vlad))
    app.add_handler(CommandHandler("vlad", vlad))

    print("Бот запущен.")
    app.run_polling()


if __name__ == "__main__":
    main()
