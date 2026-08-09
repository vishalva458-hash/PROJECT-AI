import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'super-secret-interview-prep-key-2026'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///interview_prep.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Upload configurations
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads', 'resumes')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB max limit
    ALLOWED_EXTENSIONS = {'pdf'}

    # Gemini API key (optional)
    GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
