import os
import telebot
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes


# py-telegram-bot
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(f'Hello {update.effective_user.first_name}')

# telebot
bot = telebot.TeleBot(os.environ.get("BOT_TOKEN"))

@bot.message_handler(commands=['hello'])
def send_welcome(message):
	bot.reply_to(message, "Howdy, how are you doing?")


def main() -> None:
    """Start the bot."""
    # Create the Application and pass it your bot's token.
    application = ApplicationBuilder().token(os.environ.get("BOT_TOKEN")).build()

    # on different commands - answer in Telegram
    application.add_handler(CommandHandler("start", start))

    import threading

    # Run the bot until the user presses Ctrl-C
    application.run_polling()

    telebot_thread = threading.Thread(target=bot.polling)
    telebot_thread.start()


if __name__ == "__main__":
    main()
