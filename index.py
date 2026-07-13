import os
import sys
import traceback
from flask import Flask
from dotenv import load_dotenv
load_dotenv()

sys.path.append(os.path.abspath(os.path.dirname(__file__))) # to load imports once instead in everytime it's imported

def get_application():
    from app import create_app
    return create_app()


app = get_application()

if __name__ == '__main__':
    app.run(debug=True)
