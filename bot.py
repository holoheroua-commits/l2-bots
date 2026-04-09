import pandas as pd
import datetime
import pytz
import json

from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes


TOKEN = "8297475538:AAE5ZSQSz3x-Ly6Gq1D-_F7yEDfCeuKXpy8"

CSV_URL = "https://docs.google.com/spreadsheets/d/1QMrkdAfyaaR3WLq23cvl30eCLocH4aiqo_oy3ydV44M/export?format=csv&gid=656412099"

MOSCOW_TZ = pytz.timezone("Europe/Moscow")

USERS_FILE = "users.json"


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


async def check_schedule(context: ContextTypes.DEFAULT_TYPE):

    now = datetime.datetime.now(MOSCOW_TZ)

    df = load_schedule()

    weekday = now.weekday()

    for _, row in df.iterrows():

        hour = int(row.iloc[0])

        for day_name, day_num in days_map.items():

            if weekday == day_num:

                event = str(row[day_name])

                if event == "nan":
                    continue

                if now.minute == 55 and now.hour == hour - 1:

                    await send_to_all(
                        context,
                        f"⏰ Через 5 минут начнётся: {event}"
                    )

                if now.minute == 0 and now.hour == hour:

                    await send_to_all(
                        context,
                        f"📢 Началось событие: {event}"
                    )


def main():

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stop", stop))
    app.add_handler(CommandHandler("today", today))

    app.job_queue.run_repeating(
        check_schedule,
        interval=60,
        first=5
    )

    print("SCHEDULE BOT STARTED")

    app.run_polling()


if __name__ == "__main__":
    main()
