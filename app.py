from flask import Flask, request
from telegram import Update
from python-telegram-bot import application  # Assuming your main bot logic is in main_bot.py
from keep_alive import start_keep_alive
import os

app = Flask(__name__)

@app.route('/api/webhook', methods=['POST'])
def webhook():
    if request.method == "POST":
        update = Update.de_json(request.get_json(force=True), application.bot)
        application.process_update(update)
        return 'ok', 200
    return 'error', 404

if __name__ == "__main__":
    url = os.getenv("KEEP_ALIVE_URL", "https://clinic-finder-k4pj.onrender.com")  # Update with your Render URL
    start_keep_alive(url)
    app.run(port=5000, debug=True)
