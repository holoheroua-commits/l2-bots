import os
import pandas as pd
import datetime
import pytz
import json

from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes


TOKEN = os.getenv("TOKEN")

PORT = int(os.getenv("PORT", 8080))

WEBHOOK_URL = "https://sweet-exploration-production-7cb4.up.railway.app"


CSV_URL = "https://docs.google.com/spreadsheets/d/1QMrkdAfyaaR3WLq23cvl30eCLocH4aiqo_oy3ydV44M/export?format=csv&gid=656412099"

MOSCOW_TZ = pytz.timezone("Europe/Moscow")

USERS_FILE = "/data/users.json"


days_map = {
    "Понедельник": 0,
    "Вторник": 1,
    "Среда": 2,
    "Четверг": 3,
    "Пятница": 4,
    "Суббота": 5,
    "Воскресенье": 6
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


async def send_to_all(context, text):
    for user in users:
        try:
            await context.bot.send_message(chat_id=user, text=text)
        except:
            pass


# ВАЖНО: функция должна быть async
async def schedule_jobs(app):

    df = load_schedule()

    for _, row in df.iterrows():

        hour = int(row.iloc[0])

        for day_name, weekday_number in days_map.items():

            event = row[day_name]

            if pd.notna(event):

                # уведомление в момент события
                app.job_queue.run_daily(
                    lambda context, e=event:
                    context.application.create_task(
                        send_to_all(context, f"📢 Началось событие: {e}")
                    ),

                    time=datetime.time(
                        hour=hour,
                        minute=0,
                        tzinfo=MOSCOW_TZ
                    ),

                    days=(weekday_number,)
                )

                # уведомление за 5 минут
                before_hour = hour if hour > 0 else 23
                before_minute = 55 if hour > 0 else 55

                app.job_queue.run_daily(
                    lambda context, e=event:
                    context.application.create_task(
                        send_to_all(context, f"⏰ Через 5 минут начнётся: {e}")
                    ),

                    time=datetime.time(
                        hour=before_hour - 1 if hour > 0 else 23,
                        minute=55,
                        tzinfo=MOSCOW_TZ
                    ),

                    days=(weekday_number,)
                )


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

    today_num = datetime.datetime.now(MOSCOW_TZ).weekday()

    today_name = list(days_map.keys())[today_num]

    message = "📅 Сегодня события:\n\n"

    for _, row in df.iterrows():

        hour = int(row.iloc[0])

        event = row[today_name]

        if pd.notna(event):
            message += f"{hour}:00 — {event}\n"

    await update.message.reply_text(message)


def main():

    app = (
        ApplicationBuilder()
        .token(TOKEN)
        .post_init(schedule_jobs)
        .build()
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stop", stop))
    app.add_handler(CommandHandler("today", today))

    print("WEBHOOK SCHEDULE BOT STARTED OK")

    app.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path=TOKEN,
        webhook_url=f"{WEBHOOK_URL}/{TOKEN}"
    )


if __name__ == "__main__":
    main()
