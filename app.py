from flask import Flask, request
from telegram import Update
from python-telegram-bot import main
from keep_alive import start_keep_alive
import os

app = Flask(__name__)

# Set environment variables (these should be set in your Render service settings)
BOT_TOKEN = os.environ.get("BOT_TOKEN")

# Initialize the bot application
application = main(BOT_TOKEN)

@app.route('/api/webhook', methods=['POST'])
def webhook():
    if request.method == "POST":
        update = Update.de_json(request.get_json(force=True), application.bot)
        application.process_update(update)
        return 'ok', 200
    return 'error', 404

if __name__ == "__main__":
    start_keep_alive()
    app.run(port=5000, debug=True)
