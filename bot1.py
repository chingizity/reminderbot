import logging
from datetime import datetime, time
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
)
BOT_TOKEN = "8847835270:AAFuyfdhlgn030rZbHFCuvcYKzzYYm6Ybr8"
CHAT_ID = 5724756801

# BOT_TOKEN = "8203402267:AAFRKSIxihE1tmZzlcF636MFWl6cTNr6lF0"
# CHAT_ID = 5481777055

EAT_INTERVAL = 2  # секунд (3 минуты)
EAT_JOB_NAME = "eat_check"

REMINDERS = [
    (4, 1, "Привет! А ты знала, что ты моя попажопа!"),
    (5, 0, "Таблетки!!!!!!! \n Антидепрессанты."),
    (7, 0, "Солнышко, твой максимум калорий: 1600-1700, у тебя есть весы и надо фоткать еду!!!"),
    (9, 0, "Солнышко, твой максимум калорий: 1600-1700, у тебя есть весы и надо фоткать еду!!!"),
    (11, 0, "Солнышко, твой максимум калорий: 1600-1700, у тебя есть весы и надо фоткать еду!!!"),
    (14, 0, "Солнышко, твой максимум калорий: 1600-1700, у тебя есть весы и надо фоткать еду!!!"),
    (16, 0, "Солнышко, твой максимум калорий: 1600-1700, у тебя есть весы и надо фоткать еду!!!"),
    (16, 0, "Таблетки!!!!!!! \n усыпушки"),
    (18, 0, "Наступает ночь. Прекрасная моя Юнона засыпает. Сладких снов моей любимой девочке. Лублу типя всем своим сердцем!!"),
]

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


def build_keyboard() -> InlineKeyboardMarkup:
    button = InlineKeyboardButton("✅ Выполнено", callback_data="done")
    return InlineKeyboardMarkup([[button]])


def build_eat_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("✅ Наелась", callback_data="eat_full"),
        InlineKeyboardButton("🍽 Ещё нет", callback_data="eat_more"),
    ]])


def format_duration(seconds: float) -> str:
    minutes, secs = divmod(int(seconds), 60)
    return f"{minutes} мин {secs} сек"


async def send_reminder(context: ContextTypes.DEFAULT_TYPE) -> None:
    text = context.job.data
    await context.bot.send_message(
        chat_id=CHAT_ID, text=text, reply_markup=build_keyboard()
    )


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    if query.data == "done":
        original_text = query.message.text
        await query.edit_message_text(
            text=f"{original_text}\n\n✅ Отмечено как выполнено!"
        )


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    await update.message.reply_text(
        f"{chat_id}"
    )


async def test_reminder(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    for _, _, text in REMINDERS:
        await update.message.reply_text(text, reply_markup=build_keyboard())


async def eat_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if context.bot_data.get("eat_session"):
        await update.message.reply_text("🍽 Сессия еды уже идёт, я слежу за временем!")
        return

    context.bot_data["eat_session"] = {"start": datetime.now(), "checks": 0}
    context.job_queue.run_once(
        eat_check, EAT_INTERVAL, chat_id=CHAT_ID, name=EAT_JOB_NAME
    )
    await update.message.reply_text(
        "🍽 Приятного аппетита!\n⏱ Засекла время, спрошу через 3 минуты."
    )


async def eat_check(context: ContextTypes.DEFAULT_TYPE) -> None:
    session = context.bot_data.get("eat_session")
    if not session:
        return

    session["checks"] += 1
    elapsed = (datetime.now() - session["start"]).total_seconds()
    await context.bot.send_message(
        chat_id=CHAT_ID,
        text=f"🍽 Прошло {format_duration(elapsed)}.\nТы наелась?",
        reply_markup=build_eat_keyboard(),
    )


async def eat_button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    original_text = query.message.text
    session = context.bot_data.get("eat_session")

    if not session:
        await query.edit_message_text(f"{original_text}\n\n⚠️ Эта сессия уже завершена.")
        return

    if query.data == "eat_full":
        for job in context.job_queue.get_jobs_by_name(EAT_JOB_NAME):
            job.schedule_removal()

        elapsed = (datetime.now() - session["start"]).total_seconds()
        context.bot_data.pop("eat_session")
        await query.edit_message_text(
            text=(
                f"{original_text}\n\n"
                f"✅ Наелась! Умничка 💛\n"
                f"⏱ Сессия еды: {format_duration(elapsed)}\n"
                f"🔔 Проверок: {session['checks']}"
            )
        )
    else:  # eat_more
        context.job_queue.run_once(
            eat_check, EAT_INTERVAL, chat_id=CHAT_ID, name=EAT_JOB_NAME
        )
        await query.edit_message_text(
            text=f"{original_text}\n\n🍽 Ещё не наелась. Спрошу снова через 3 минуты ⏱"
        )


def main() -> None:
    application = Application.builder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("test", test_reminder))
    application.add_handler(CommandHandler("eat", eat_start))
    application.add_handler(CallbackQueryHandler(eat_button_handler, pattern="^eat_"))
    application.add_handler(CallbackQueryHandler(button_handler, pattern="^done$"))

    job_queue = application.job_queue
    for hour, minute, text in REMINDERS:
        job_queue.run_daily(
            send_reminder,
            time=time(hour=hour, minute=minute),
            chat_id=CHAT_ID,
            data=text,
            name=f"reminder_{hour:02d}_{minute:02d}",
        )

    logger.info("Бот запущен.")
    application.run_polling()


if __name__ == "__main__":
    main()
