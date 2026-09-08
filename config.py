import os

class DevelopmentConfig:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key-here-change-in-production'
    FLASK_ENV = os.environ.get('FLASK_ENV') or 'development'
    
    # Handle DATABASE_URL from Neon or default to SQLite
    database_url = os.environ.get('DATABASE_URL') or 'sqlite:///finance.db'
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
        
    SQLALCHEMY_DATABASE_URI = database_url
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SESSION_COOKIE_SECURE = False
    
    # OAuth Configurations
    GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID')
    GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET')

config = {
    'development': DevelopmentConfig,
    'default': DevelopmentConfig
}
