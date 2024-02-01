import logging

from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)


# region local functions
def get_tocken() -> str:
    try:
        with open("./src/token.txt", "r") as f:
            return f.readline()
    except:
        logging.error("Problem with token")
    return ""


# endregion
# region telegram functions
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=update.effective_chat.id, text="I'm a bot, please talk to me!"
    )


async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=update.effective_chat.id, text=update.message.text
    )


# endregion


# main function
def main():
    token = get_tocken()
    if token:
        application = ApplicationBuilder().token(token).build()
        start_handler = CommandHandler("start", start)
        echo_handler = MessageHandler(filters.TEXT & (~filters.COMMAND), echo)
        application.add_handler(start_handler)
        application.add_handler(echo_handler)
        application.run_polling()


# Local execution
if __name__ == "__main__":
    main()
