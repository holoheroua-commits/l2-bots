import os
import datetime
import pytz
import json

from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes


TOKEN = os.getenv("TOKEN")

PORT = int(os.getenv("PORT", 8080))

WEBHOOK_URL = "https://l2-bots-production.up.railway.app"


MOSCOW_TZ = pytz.timezone("Europe/Moscow")

USERS_FILE = "timer_users.json"


EXCLUDED = {
    0: [(21, 22)],
    1: [(19, 20), (22, 23)],
    2: [(21, 22)],
    3: [(19, 20), (22, 23)],
    4: [(21, 22)],
    5: [(18, 19)],
    6: [(19, 20)],
}


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


def allowed_now():
    now = datetime.datetime.now(MOSCOW_TZ)

    weekday = now.weekday()
    hour = now.hour

    if weekday in EXCLUDED:
        for start, end in EXCLUDED[weekday]:
            if start <= hour < end:
                return False

    return True


def is_exact_timer_minute(now):
    return now.minute % 7 == 0


async def send_timer(context: ContextTypes.DEFAULT_TYPE):
    now = datetime.datetime.now(MOSCOW_TZ)

    if not allowed_now():
        return

    if not is_exact_timer_minute(now):
        return

    for user in users:
        try:
            await context.bot.send_message(
                chat_id=user,
                text="Регайся на арену"
            )
        except:
            pass


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id

    if chat_id not in users:
        users.append(chat_id)
        save_users(users)

    await update.message.reply_text(
        "✅ Таймер включён"
    )


async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id

    if chat_id in users:
        users.remove(chat_id)
        save_users(users)

    await update.message.reply_text(
        "❌ Таймер отключён"
    )


def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stop", stop))

    # проверяем каждую минуту
    app.job_queue.run_repeating(
        send_timer,
        interval=60,
        first=10
    )

    print("WEBHOOK TIMER BOT STARTED OK")

    app.run_webhook(
    listen="0.0.0.0",
    port=PORT,
    webhook_url=f"{WEBHOOK_URL}/{TOKEN}"
)


if __name__ == "__main__":
    main()
