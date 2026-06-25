import os
import sys
import traceback
from flask import Flask
from dotenv import load_dotenv

# Load environment variables from .env (SECRET_KEY, MAIL_USERNAME, MAIL_PASSWORD, etc.)
load_dotenv()

# Make the project root importable so 'from app import ...' works regardless of how the server is started
sys.path.append(os.path.abspath(os.path.dirname(__file__)))


def get_application():
    # Attempt to build the real Flask app via the factory in app/__init__.py
    try:
        from app import create_app
        return create_app()
    except Exception:
        # If startup fails (e.g. missing config, import error), return a minimal fallback app
        # that shows the traceback in the browser instead of crashing the server silently
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


# Build the app at module load time (gunicorn imports this file and uses the `app` variable)
app = get_application()

if __name__ == '__main__':
    app.run(debug=True)
