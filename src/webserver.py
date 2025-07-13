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
    else:  # Local development - disable debug mode when running in thread
        app.run(host='0.0.0.0', port=8080, debug=False, use_reloader=False)

def keep_alive():
    t = Thread(target=run)
    t.daemon = True  # Make it a daemon thread so it doesn't block shutdown
    t.start()
