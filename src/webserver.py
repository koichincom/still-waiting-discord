from flask import Flask
from threading import Thread
import os

app = Flask('')

@app.route('/')
def home():
    return "The web server is running!"

def run():
    # Use production server in deployment, development server locally
    if os.getenv('RENDER'):  # Render environment
        from waitress import serve
        serve(app, host='0.0.0.0', port=8080)
    else:  # Local development
        app.run(host='0.0.0.0', port=8080, debug=True)

def keep_alive():
    t = Thread(target=run)
    t.start()
