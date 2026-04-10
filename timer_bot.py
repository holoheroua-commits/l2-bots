import datetime
import pytz
import json

from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes


TOKEN = "8786027118:AAG4URfFxnF8bgTxfBReCMvtH3aEor4vyGE"

MOSCOW_TZ = pytz.timezone("Europe/Moscow")

USERS_FILE = r"D:\timer_bot\users_timer.json"


EXCLUDED = {
    0: [(21, 22)],
    1: [(19, 20), (22, 23)],
    2: [(21, 22)],
    3: [(19, 20), (22, 23)],
    4: [(21, 22)],
    5: [(18, 19)],
    6: [(19, 20)]
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


def allowed_now():

    now = datetime.datetime.now(MOSCOW_TZ)

    weekday = now.weekday()
    hour = now.hour

    if weekday in EXCLUDED:
        for start, end in EXCLUDED[weekday]:
            if start <= hour < end:
                return False

    return True


async def send_timer(context: ContextTypes.DEFAULT_TYPE):

    if not allowed_now():
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
        "✅ Ты подписан на таймер каждые 7 минут"
    )


async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):

    chat_id = update.message.chat_id

    if chat_id in users:
        users.remove(chat_id)
        save_users(users)

    await update.message.reply_text(
        "❌ Ты отписан от таймера"
    )


def schedule_jobs(app):

    minutes = [0, 7, 14, 21, 28, 35, 42, 49, 56]

    for minute in minutes:

        app.job_queue.run_daily(
            send_timer,
            time=datetime.time(
                hour=0,
                minute=minute,
                tzinfo=MOSCOW_TZ
            )
        )

        for hour in range(1, 24):

            app.job_queue.run_daily(
                send_timer,
                time=datetime.time(
                    hour=hour,
                    minute=minute,
                    tzinfo=MOSCOW_TZ
                )
            )


def main():

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stop", stop))

    schedule_jobs(app)

    print("TIMER BOT STARTED OK")

    app.run_polling()


if __name__ == "__main__":
    main()