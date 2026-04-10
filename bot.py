import os
import json
import datetime
import pytz
import asyncio

from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes
)

from aiohttp import web


TOKEN = os.getenv("TOKEN")

PORT = int(os.getenv("PORT", 8080))

WEBHOOK_URL = "https://sweet-exploration-production-7cb4.up.railway.app"


MOSCOW_TZ = pytz.timezone("Europe/Moscow")

USERS_FILE = "users.json"


def load_users():

    try:
        with open(USERS_FILE, "r") as f:
            return json.load(f)

    except:

        with open(USERS_FILE, "w") as f:
            json.dump([], f)

        return []


def save_users(users):

    with open(USERS_FILE, "w") as f:
        json.dump(users, f)


users = load_users()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    chat_id = update.message.chat_id

    if chat_id not in users:

        users.append(chat_id)
        save_users(users)

    await update.message.reply_text("Ты подписан на уведомления")


async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):

    chat_id = update.message.chat_id

    if chat_id in users:

        users.remove(chat_id)
        save_users(users)

    await update.message.reply_text("Ты отписан")


async def send_schedule(context: ContextTypes.DEFAULT_TYPE):

    now = datetime.datetime.now(MOSCOW_TZ)

    if now.minute != 0:
        return

    for user in users:

        try:

            await context.bot.send_message(
                chat_id=user,
                text="Время регистрации"
            )

        except:
            pass


async def main():

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stop", stop))

    app.job_queue.run_repeating(
        send_schedule,
        interval=60,
        first=10
    )

    await app.initialize()

    await app.bot.set_webhook(
        url=f"{WEBHOOK_URL}/{TOKEN}"
    )

    runner = web.AppRunner(app.web_app())

    await runner.setup()

    site = web.TCPSite(
        runner,
        "0.0.0.0",
        PORT
    )

    await site.start()

    print("WEBHOOK BOT STARTED OK")

    await asyncio.Event().wait()


if __name__ == "__main__":

    asyncio.run(main())
