from flask import Flask, request
from telegram import Update
from main_bot import application
from keep_alive import keep_alive  # Import the keep_alive function

app = Flask(__name__)

@app.route('/api/webhook', methods=['POST'])
def webhook():
    if request.method == "POST":
        update = Update.de_json(request.get_json(force=True), application.bot)
        application.process_update(update)
        return 'ok', 200
    return 'error', 404

if __name__ == "__main__":
    keep_alive()  # Start the keep-alive function
    app.run(port=5000, debug=True)
