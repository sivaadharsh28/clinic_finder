from flask import Flask, request
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ConversationHandler
import pandas as pd
import googlemaps
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os

app = Flask(__name__)

# Initialize the Telegram bot
TOKEN = os.getenv("BOT_TOKEN")
application = Application.builder().token(TOKEN).build()

# Define your bot handlers here...

@app.route('/api/webhook', methods=['POST'])
def webhook():
    if request.method == "POST":
        update = Update.de_json(request.get_json(force=True), application.bot)
        application.process_update(update)
        return 'ok', 200
    return 'error', 404

if __name__ == "__main__":
    app.run(port=5000, debug=True)
