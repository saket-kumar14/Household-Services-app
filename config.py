import os



curr_dir = os.path.dirname(os.path.abspath(__file__))

class Config:
    SQLALCHEMY_DATABASE_URI = "sqlite:///db.sqlite3"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = 'supersecretkey'
    PASSWORD_HASH= 'sha512'

    UPLOAD_EXTENSIONS = ['.pdf']
    UPLOAD_PATH = os.path.join(curr_dir, 'static', "pdfs")