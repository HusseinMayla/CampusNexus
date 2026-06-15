import os
import sys
import traceback
from flask import Flask
from dotenv import load_dotenv
load_dotenv()

sys.path.append(os.path.abspath(os.path.dirname(__file__))) # to load imports once instead in everytime it's imported

def get_application():
    try:
        from app import create_app
        return create_app()
    except Exception:
#Instead of crashing it catches the error and return an html page
        err_info = traceback.format_exc()
        print(f"CRITICAL STARTUP ERROR:\n{err_info}", file=sys.stderr)
        fallback = Flask(__name__)
        @fallback.route('/')
        @fallback.route('/<path:path>')
        def error_page(path=""):
            return f"""
            <h1>Deployment Startup Error</h1>
            <pre>{err_info}</pre>
            """, 500
        return fallback

app = get_application()

if __name__ == '__main__':
    from app.extensions import socketio
    socketio.run(app, debug=True) #socket for live chats
