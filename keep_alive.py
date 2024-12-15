import threading
import time
import requests

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
        time.sleep(600)  

def start_keep_alive(url):
    keep_alive_thread = threading.Thread(target=keep_alive, args=(url,))
    keep_alive_thread.daemon = True
    keep_alive_thread.start()
