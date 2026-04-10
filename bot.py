import os
import pandas as pd
import datetime
import pytz
import json
import asyncio

from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes


TOKEN = os.getenv("TOKEN")

PORT = int(os.getenv("PORT", 8080))

WEBHOOK_URL = "https://sweet-exploration-production-7cb4.up.railway.app"


CSV_URL = "https://docs.google.com/spreadsheets/d/1QMrkdAfyaaR3WLq23cvl30eCLocH4aiqo_oy3ydV44M/export?format=csv&gid=656412099"

MOSCOW_TZ = pytz.timezone("Europe/Moscow")

USERS_FILE = "/data/users.json"


days_map = {
    0: "Понедельник",
    1: "Вторник",
    2: "Среда",
    3: "Четверг",
    4: "Пятница",
    5: "Суббота",
    6: "Воскресенье"
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


def load_schedule():
    return pd.read_csv(CSV_URL)


async def send_to_all(bot, text):

    for user in users:

        try:
            await bot.send_message(chat_id=user, text=text)

        except:
            pass


async def scheduler_loop(app):

    last_checked_minute = None

    while True:

        now = datetime.datetime.now(MOSCOW_TZ)

        if now.minute != last_checked_minute:

            last_checked_minute = now.minute

            df = load_schedule()

            weekday_name = days_map[now.weekday()]

            for _, row in df.iterrows():

                hour = int(row.iloc[0])

                event = row[weekday_name]

                if pd.notna(event):

                    event = str(event)

                    # уведомление за 5 минут
                    before_hour = (hour - 1) % 24

                    if now.hour == before_hour and now.minute == 55:

                        await send_to_all(
                            app.bot,
                            f"⏰ Через 5 минут начнётся: {event}"
                        )

                    # уведомление в момент события
                    if now.hour == hour and now.minute == 0:

                        await send_to_all(
                            app.bot,
                            f"📢 Началось событие: {event}"
                        )

        await asyncio.sleep(5)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    chat_id = update.message.chat_id

    if chat_id not in users:

        users.append(chat_id)

        save_users(users)

    await update.message.reply_text(
        "✅ Ты подписан на уведомления расписания"
    )


async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):

    chat_id = update.message.chat_id

    if chat_id in users:

        users.remove(chat_id)

        save_users(users)

    await update.message.reply_text(
        "❌ Ты отписан от уведомлений"
    )


async def today(update: Update, context: ContextTypes.DEFAULT_TYPE):

    df = load_schedule()

    today_name = days_map[
        datetime.datetime.now(MOSCOW_TZ).weekday()
    ]

    message = "📅 Сегодня события:\n\n"

    for _, row in df.iterrows():

        hour = int(row.iloc[0])

        event = row[today_name]

        if pd.notna(event):

            message += f"{hour}:00 — {event}\n"

    await update.message.reply_text(message)


async def post_init(app):

    asyncio.create_task(
        scheduler_loop(app)
    )


def main():

    app = (
        ApplicationBuilder()
        .token(TOKEN)
        .post_init(post_init)
        .build()
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stop", stop))
    app.add_handler(CommandHandler("today", today))

    print("SCHEDULE LOOP STARTED")

    app.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path=TOKEN,
        webhook_url=f"{WEBHOOK_URL}/{TOKEN}"
    )


if __name__ == "__main__":
    main()
