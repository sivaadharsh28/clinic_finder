from flask import Flask, request
from telegram_bot import handle_update

app = Flask(__name__)

@app.route('/webhook', methods=['POST'])
def webhook():
    handle_update(request.get_json())
    return 'OK', 200

if __name__ == '__main__':
    app.run(port=5000, debug=True)
 
