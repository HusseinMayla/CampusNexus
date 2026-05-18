import traceback
import sys
from flask import Flask

try:
    from app import create_app
    app = create_app()
except Exception:
    print("CRITICAL: Failed to initialize application", file=sys.stderr)
    traceback.print_exc()
    
    # Fallback app to display the error on Vercel
    app = Flask(__name__)
    
    @app.route('/')
    @app.route('/<path:path>')
    def catch_all(path=""):
        error_info = traceback.format_exc()
        return f"""
        <h1>Application Startup Error</h1>
        <p>The application failed to start on Vercel. Here is the traceback:</p>
        <pre>{error_info}</pre>
        """, 500

if __name__ == '__main__':
    app.run(debug=True)
