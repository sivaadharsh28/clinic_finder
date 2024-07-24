from flask import Flask, request
from telegram import Bot, Update
from telegram.ext import Dispatcher, CommandHandler, MessageHandler, Filters
import logging
import os

app = Flask(__name__)

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

logger = logging.getLogger(__name__)

# Initialize the bot
BOT_TOKEN = os.getenv('BOT_TOKEN')
bot = Bot(token=BOT_TOKEN)

# Set up dispatcher
dispatcher = Dispatcher(bot, None, use_context=True)

# Define a few command handlers
def start(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text="Hello, I am your bot!")

dispatcher.add_handler(CommandHandler("start", start))

@app.route('/api/webhook', methods=['POST'])
def webhook():
    if request.method == "POST":
        update = Update.de_json(request.get_json(force=True), bot)
        dispatcher.process_update(update)
        return 'ok'

if __name__ == "__main__":
    app.run(port=5000)
