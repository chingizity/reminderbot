import logging
from datetime import time
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
)

BOT_TOKEN = "8847835270:AAFuyfdhlgn030rZbHFCuvcYKzzYYm6Ybr8"
CHAT_ID = 5724756801

REMINDERS = [
    (4, 0, "Таблетки!!!!!!! \n Антидепрессанты."),
    (5, 0, "Таблетки!!!!!!! \n   1-я таблетка"),
    (7, 0, "Таблетки!!!!!!! \n 2-я таблетка"),
    (9, 0, "Таблетки!!!!!!! \n 3-я таблетка"),
    (11, 0, "Таблетки!!!!!!! \n 4-я таблетка"),
    (13, 0, "Таблетки!!!!!!! \n 5-я таблетка"),
    (15, 0, "Таблетки!!!!!!! \n 6-я таблетка"),
    (17, 0, "Таблетки!!!!!!! \n усыпушки"),
    (18, 0, "А вот это уже не про таблетки, просто хотел напомнить, что очень-очень люблю тебя, солнышко моё! :>"),
]

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


def build_keyboard() -> InlineKeyboardMarkup:
    button = InlineKeyboardButton("✅ Выполнено", callback_data="done")
    return InlineKeyboardMarkup([[button]])


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



def main() -> None:
    application = Application.builder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("test", test_reminder))
    application.add_handler(CallbackQueryHandler(button_handler))

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
