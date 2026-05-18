import os
import sys
import traceback
from flask import Flask

# Add the current directory to sys.path to ensure the 'app' package is found correctly
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

def get_application():
    try:
        from app import create_app
        return create_app()
    except Exception:
        # Capture the error and return a fallback app to display it
        err_info = traceback.format_exc()
        print(f"CRITICAL STARTUP ERROR:\n{err_info}", file=sys.stderr)
        
        fallback = Flask(__name__)
        @fallback.route('/')
        @fallback.route('/<path:path>')
        def error_page(path=""):
            return f"""
            <h1>Deployment Startup Error</h1>
            <p>The application failed to initialize on Vercel.</p>
            <pre>{err_info}</pre>
            """, 500
        return fallback

# Vercel's Python builder specifically looks for a top-level variable named 'app' or 'application'
app = get_application()

if __name__ == '__main__':
    app.run(debug=True)
