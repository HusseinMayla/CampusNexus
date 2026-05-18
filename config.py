import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'
    basedir = os.path.abspath(os.path.dirname(__file__))
    # For Vercel/Serverless, we use /tmp for SQLite if needed, or ensure the folder exists
    db_path = os.path.join(basedir, 'instance', 'database.db')
    
    # Create the instance folder if it doesn't exist (local dev)
    if not os.path.exists(os.path.join(basedir, 'instance')):
        try:
            os.makedirs(os.path.join(basedir, 'instance'))
        except:
            # If on Vercel, this might fail, so we point to /tmp
            db_path = '/tmp/database.db'

    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + db_path
    SQLALCHEMY_TRACK_MODIFICATIONS = False
