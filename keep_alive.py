from flask import Flask
from threading import Thread
import os # <--- Add this import

app = Flask('')

@app.route('/')
def home():
    return "Bot is running perfectly!"

def run():
    # Render assigns a dynamic port, so we catch it here. Defaults to 8080.
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run)
    t.start()