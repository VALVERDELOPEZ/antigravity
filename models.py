"""
Lead Finder AI - Database Models
"""
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import UserMixin
# from sqlalchemy.dialects.postgresql import ARRAY

db = SQLAlchemy()
bcrypt = Bcrypt()


class User(db.Model, UserMixin):
    """User model for authentication and subscription"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    name = db.Column(db.String(100))
    onboarding_completed = db.Column(db.Boolean, default=False)
    
    # Subscription
    plan = db.Column(db.String(20), default='free')  # free, starter, pro, enterprise
    stripe_customer_id = db.Column(db.String(255))
    stripe_subscription_id = db.Column(db.String(255))
    subscription_status = db.Column(db.String(20), default='active')  # active, canceled, past_due
    subscription_end_date = db.Column(db.DateTime)
    
    # Settings
    keywords = db.Column(db.Text, default='looking for developer, need help with, struggling with, anyone know, recommendations for')
    platforms = db.Column(db.Text, default='reddit')  # comma-separated
    email_signature = db.Column(db.Text)
    
    # Tracking
    leads_found_count = db.Column(db.Integer, default=0)
    emails_sent_count = db.Column(db.Integer, default=0)
    emails_opened_count = db.Column(db.Integer, default=0)
    emails_replied_count = db.Column(db.Integer, default=0)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login_at = db.Column(db.DateTime)
    
    # Referral System (PLG)
    referral_code = db.Column(db.String(20))
    referred_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    total_referrals = db.Column(db.Integer, default=0)
    referral_tier = db.Column(db.String(20), default='none')
    
    # Relationships
    leads = db.relationship('Lead', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    transactions = db.relationship('Transaction', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    
    def set_password(self, password):
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
    
    def check_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)
    
    def get_keywords_list(self):
        return [k.strip() for k in self.keywords.split(',') if k.strip()]
    
    def get_platforms_list(self):
        return [p.strip() for p in self.platforms.split(',') if p.strip()]
    
    def to_dict(self):
        return {
            'id': self.id,
            'email': self.email,
            'name': self.name,
            'plan': self.plan,
            'subscription_status': self.subscription_status,
            'leads_found_count': self.leads_found_count,
            'emails_sent_count': self.emails_sent_count,
            'emails_opened_count': self.emails_opened_count,
            'emails_replied_count': self.emails_replied_count,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class Lead(db.Model):
    """Lead model for scraped and qualified leads"""
    __tablename__ = 'leads'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    
    # Lead Info
    name = db.Column(db.String(255))
    username = db.Column(db.String(255))
    email = db.Column(db.String(255))
    platform = db.Column(db.String(50))  # reddit, twitter, hackernews, indiehackers, etc.
    profile_url = db.Column(db.Text)
    post_url = db.Column(db.Text)
    
    # Scraping metadata
    external_id = db.Column(db.String(100))  # ID from the source platform (e.g., Reddit post ID)
    source = db.Column(db.String(100))  # Subreddit name, 'Show HN', etc.
    language = db.Column(db.String(5))  # ISO language code: en, es, pt, fr
    
    # Content
    title = db.Column(db.Text)
    content = db.Column(db.Text)
    problem_summary = db.Column(db.Text)
    
    # AI Scoring
    score = db.Column(db.Integer, default=0)  # 1-10
    urgency = db.Column(db.Integer, default=0)  # 1-10
    budget_indicator = db.Column(db.String(20))  # low, medium, high, enterprise
    market_size = db.Column(db.String(20))  # small, medium, large
    willingness_to_pay = db.Column(db.Integer, default=0)  # 1-10
    pain_points = db.Column(db.Text)  # JSON array of pain points
    
    # Email
    email_generated = db.Column(db.Text)
    email_subject = db.Column(db.String(255))
    email_sent = db.Column(db.Boolean, default=False)
    email_sent_at = db.Column(db.DateTime)
    email_opened = db.Column(db.Boolean, default=False)
    email_opened_at = db.Column(db.DateTime)
    email_replied = db.Column(db.Boolean, default=False)
    email_replied_at = db.Column(db.DateTime)
    last_reply_body = db.Column(db.Text)
    
    # Email Tracking (PRO)
    email_tracking_id = db.Column(db.String(50))
    email_clicked = db.Column(db.Boolean, default=False)
    email_clicked_at = db.Column(db.DateTime)
    
    # Social Enrichment (PRO)
    linkedin_url = db.Column(db.Text)
    twitter_url = db.Column(db.Text)
    github_url = db.Column(db.Text)
    company_name = db.Column(db.String(255))
    company_domain = db.Column(db.String(255))
    company_size = db.Column(db.String(50))
    company_industry = db.Column(db.String(100))
    enriched_at = db.Column(db.DateTime)
    
    # Status
    status = db.Column(db.String(20), default='new')  # new, contacted, replied, converted, archived
    source_type = db.Column(db.String(20), default='real')  # 'real' (scraped), 'ai_generated', 'demo'
    notes = db.Column(db.Text)
    
    # Timestamps
    source_created_at = db.Column(db.DateTime)  # When the original post was created
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name or self.username,
            'username': self.username,
            'email': self.email,
            'platform': self.platform,
            'profile_url': self.profile_url,
            'post_url': self.post_url,
            'external_id': self.external_id,
            'source': self.source,
            'language': self.language,  # ISO code: en, es, pt, fr
            'title': self.title,
            'content': self.content[:200] + '...' if self.content and len(self.content) > 200 else self.content,
            'problem_summary': self.problem_summary,
            'score': self.score,
            'urgency': self.urgency,
            'budget_indicator': self.budget_indicator,
            'email_sent': self.email_sent,
            'email_opened': self.email_opened,
            'email_replied': self.email_replied,
            'status': self.status,
            'source_type': self.source_type,  # 'real', 'ai_generated', 'demo'
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class Transaction(db.Model):
    """Transaction model for payment history"""
    __tablename__ = 'transactions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    
    # Stripe
    stripe_payment_intent_id = db.Column(db.String(255))
    stripe_invoice_id = db.Column(db.String(255))
    
    # Transaction Details
    type = db.Column(db.String(20))  # subscription, one_time
    plan = db.Column(db.String(20))
    amount = db.Column(db.Float)
    currency = db.Column(db.String(3), default='EUR')
    status = db.Column(db.String(20))  # succeeded, failed, refunded
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'type': self.type,
            'plan': self.plan,
            'amount': self.amount,
            'currency': self.currency,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class AutomationLog(db.Model):
    """Log model for automation events"""
    __tablename__ = 'automation_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Event Info
    event_type = db.Column(db.String(50))  # scrape, qualify, email, error
    platform = db.Column(db.String(50))
    status = db.Column(db.String(20))  # success, failed, partial
    
    # Details
    message = db.Column(db.Text)
    leads_found = db.Column(db.Integer, default=0)
    emails_sent = db.Column(db.Integer, default=0)
    error_message = db.Column(db.Text)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    duration_seconds = db.Column(db.Float)
    
    def to_dict(self):
        return {
            'id': self.id,
            'event_type': self.event_type,
            'platform': self.platform,
            'status': self.status,
            'message': self.message,
            'leads_found': self.leads_found,
            'emails_sent': self.emails_sent,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class UserKeywords(db.Model):
    """User specific configuration for scraping"""
    __tablename__ = 'user_keywords'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    
    # Configuration
    keywords = db.Column(db.JSON)  # List of keywords
    subreddits = db.Column(db.JSON)  # List of subreddits
    languages = db.Column(db.JSON, default=['en'])  # ['en', 'es', 'pt', 'fr']
    min_score = db.Column(db.Integer, default=7)
    active_platforms = db.Column(db.JSON, default=['reddit', 'hn', 'indie_hackers'])
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'keywords': self.keywords,
            'subreddits': self.subreddits,
            'languages': self.languages,
            'min_score': self.min_score,
            'active_platforms': self.active_platforms
        }


class UserSMTPConfig(db.Model):
    """User SMTP configuration for sending emails"""
    __tablename__ = 'user_smtp_config'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    
    smtp_server = db.Column(db.String(255))
    smtp_port = db.Column(db.Integer, default=587)
    smtp_username = db.Column(db.String(255))
    smtp_password = db.Column(db.Text)  # Encrypted
    sender_name = db.Column(db.String(100))
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def get_password(self):
        from cryptography.fernet import Fernet
        import os
        key = os.getenv('ENCRYPTION_KEY')
        if not key:
            raise ValueError("ENCRYPTION_KEY not set")
        f = Fernet(key.encode() if isinstance(key, str) else key)
        return f.decrypt(self.smtp_password.encode()).decode()

    def set_password(self, password):
        from cryptography.fernet import Fernet
        import os
        key = os.getenv('ENCRYPTION_KEY')
        if not key:
             raise ValueError("ENCRYPTION_KEY not set")
        f = Fernet(key.encode() if isinstance(key, str) else key)
        self.smtp_password = f.encrypt(password.encode()).decode()
        
    def to_dict(self):
        return {
            'smtp_server': self.smtp_server,
            'smtp_port': self.smtp_port,
            'smtp_username': self.smtp_username,
            'sender_name': self.sender_name,
            'is_configured': bool(self.smtp_server and self.smtp_password)
        }
