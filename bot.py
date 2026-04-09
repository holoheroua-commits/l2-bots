import pandas as pd
import datetime
import pytz
import json
import asyncio

from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger


TOKEN = "8297475538:AAE5ZSQSz3x-Ly6Gq1D-_F7yEDfCeuKXpy8"

CSV_URL = "https://docs.google.com/spreadsheets/d/1QMrkdAfyaaR3WLq23cvl30eCLocH4aiqo_oy3ydV44M/export?format=csv&gid=656412099"

MOSCOW_TZ = pytz.timezone("Europe/Moscow")

USERS_FILE = r"D:\bot\users.json"


days_map = {
    "Понедельник": "mon",
    "Вторник": "tue",
    "Среда": "wed",
    "Четверг": "thu",
    "Пятница": "fri",
    "Суббота": "sat",
    "Воскресенье": "sun"
}


def load_users():
    try:
        with open(USERS_FILE, "r") as f:
            return json.load(f)
    except:
        return []


def save_users(users):
    with open(USERS_FILE, "w") as f:
        json.dump(users, f)


users = load_users()


def load_schedule():
    return pd.read_csv(CSV_URL)


async def send_to_all(app, text):

    for user in users:

        try:
            await app.bot.send_message(chat_id=user, text=text)
        except:
            pass


def schedule_jobs(app):

    scheduler = BackgroundScheduler(timezone=MOSCOW_TZ)

    df = load_schedule()

    for _, row in df.iterrows():

        hour = int(row.iloc[0])

        for day in days_map:

            if day in df.columns:

                event = str(row[day])

                if event != "nan":

                    scheduler.add_job(
                        lambda e=event: asyncio.run(
                            send_to_all(app, f"📢 Началось событие: {e}")
                        ),
                        CronTrigger(
                            day_of_week=days_map[day],
                            hour=hour,
                            minute=0
                        )
                    )

                    scheduler.add_job(
                        lambda e=event: asyncio.run(
                            send_to_all(app, f"⏰ Через 5 минут начнётся: {e}")
                        ),
                        CronTrigger(
                            day_of_week=days_map[day],
                            hour=hour,
                            minute=55
                        )
                    )

    scheduler.start()


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

        event = str(row[today_name])

        if event != "nan":

            message += f"{hour}:00 — {event}\n"

    await update.message.reply_text(message)


def main():

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stop", stop))
    app.add_handler(CommandHandler("today", today))

    schedule_jobs(app)

    print("SCHEDULE BOT STARTED")

    app.run_polling()


if __name__ == "__main__":
    main()