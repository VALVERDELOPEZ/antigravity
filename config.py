"""
Lead Finder AI - Configuration Module
"""
import os
from datetime import timedelta
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables (try .env first, then .env.local)
env_path = Path('.env')
if not env_path.exists():
    env_path = Path('.env.local')
load_dotenv(env_path)


class Config:
    """Base configuration"""
    # Flask - SECRET_KEY must be set via environment in production
    SECRET_KEY = os.getenv('SECRET_KEY')
    if not SECRET_KEY:
        import warnings
        warnings.warn("SECRET_KEY not set! Using insecure default for development only.")
        SECRET_KEY = 'dev-secret-key-change-me-in-production'
    
    # Rate Limiting
    RATELIMIT_HEADERS_ENABLED = True
    
    # Database - Supabase PostgreSQL or SQLite fallback
    _database_url = os.getenv('DATABASE_URL', 'sqlite:///leadfinder.db')
    # Supabase uses postgres:// but SQLAlchemy needs postgresql://
    if _database_url.startswith('postgres://'):
        _database_url = _database_url.replace('postgres://', 'postgresql://', 1)
    # Support for psycopg2 driver explicitly
    if _database_url.startswith('postgresql://') and '+psycopg2' not in _database_url:
        _database_url = _database_url.replace('postgresql://', 'postgresql+psycopg2://', 1)
    SQLALCHEMY_DATABASE_URI = _database_url
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,  # Handle stale connections
        'pool_recycle': 300,    # Recycle connections every 5 minutes
    }
    
    # Session
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    
    # Stripe
    STRIPE_SECRET_KEY = os.getenv('STRIPE_SECRET_KEY')
    STRIPE_PUBLISHABLE_KEY = os.getenv('STRIPE_PUBLISHABLE_KEY')
    STRIPE_WEBHOOK_SECRET = os.getenv('STRIPE_WEBHOOK_SECRET')
    STRIPE_PRICE_STARTER = os.getenv('STRIPE_PRICE_STARTER')
    STRIPE_PRICE_PRO = os.getenv('STRIPE_PRICE_PRO')
    
    # OpenAI
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    
    # Reddit
    REDDIT_CLIENT_ID = os.getenv('REDDIT_CLIENT_ID')
    REDDIT_CLIENT_SECRET = os.getenv('REDDIT_CLIENT_SECRET')
    REDDIT_USER_AGENT = os.getenv('REDDIT_USER_AGENT', 'LeadFinderAI/1.0')
    
    # Twitter
    TWITTER_BEARER_TOKEN = os.getenv('TWITTER_BEARER_TOKEN')
    TWITTER_API_KEY = os.getenv('TWITTER_API_KEY')
    TWITTER_API_SECRET = os.getenv('TWITTER_API_SECRET')
    
    # Email
    SMTP_SERVER = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
    SMTP_PORT = int(os.getenv('SMTP_PORT', 587))
    SMTP_USERNAME = os.getenv('SMTP_USERNAME')
    SMTP_PASSWORD = os.getenv('SMTP_PASSWORD')
    EMAIL_FROM_NAME = os.getenv('EMAIL_FROM_NAME', 'Lead Finder AI')
    EMAIL_FROM_ADDRESS = os.getenv('EMAIL_FROM_ADDRESS')
    
    # App Settings
    APP_URL = os.getenv('APP_URL', 'http://localhost:5000')
    SCRAPE_INTERVAL_HOURS = int(os.getenv('SCRAPE_INTERVAL_HOURS', 8))
    SCRAPE_INTERVAL_MINUTES = int(os.getenv('SCRAPE_INTERVAL_MINUTES', 30))  # For real-time MVP
    
    # Scraping Settings
    MIN_ENGAGEMENT_SCORE = int(os.getenv('MIN_ENGAGEMENT_SCORE', 2))  # Minimum upvotes/comments
    MAX_REQUESTS_PER_CYCLE = int(os.getenv('MAX_REQUESTS_PER_CYCLE', 20))  # Rate limiting
    
    # Plan Limits
    PLANS = {
        'free': {
            'max_leads': 10,
            'max_emails': 0,
            'auto_scrape': False,
            'platforms': ['reddit'],
            'price': 0
        },
        'starter': {
            'max_leads': 100,
            'max_emails': 50,
            'auto_scrape': True,
            'platforms': ['reddit', 'twitter', 'hackernews'],
            'price': 49
        },
        'pro': {
            'max_leads': 500,
            'max_emails': 250,
            'auto_scrape': True,
            'platforms': ['reddit', 'twitter', 'hackernews', 'linkedin', 'discord', 'indiehackers'],
            'price': 99
        },
        'enterprise': {
            'max_leads': -1,  # Unlimited
            'max_emails': -1,
            'auto_scrape': True,
            'platforms': 'all',
            'price': 'custom'
        }
    }


class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    SQLALCHEMY_ECHO = True


class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    SQLALCHEMY_ECHO = False


class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
