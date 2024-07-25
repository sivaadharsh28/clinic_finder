from flask import Flask, request
import threading
import time
import requests
import os

app = Flask(__name__)

@app.route('/')
def home():
    return 'Welcome to the Telegram Bot API', 200

@app.route('/api/webhook', methods=['POST'])
def webhook():
    return 'Webhook not configured', 200

def keep_alive(url):
    while True:
        try:
            response = requests.get(url)
            if response.status_code == 200:
                print("Keep-alive request successful.")
            else:
                print(f"Keep-alive request failed with status code {response.status_code}.")
        except Exception as e:
            print(f"Error in keep-alive request: {e}")
        time.sleep(600)  # Wait for 10 minutes before sending the next request

def start_keep_alive(url):
    keep_alive_thread = threading.Thread(target=keep_alive, args=(url,))
    keep_alive_thread.daemon = True
    keep_alive_thread.start()

keep_alive_url = os.getenv("KEEP_ALIVE_URL", "https://clinic-finder-k4pj.onrender.com")
start_keep_alive(keep_alive_url)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)
