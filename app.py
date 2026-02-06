"""
Lead Finder AI - Main Flask Application
"""
import os
import logging
from logging.handlers import RotatingFileHandler
from flask import Flask, render_template, jsonify
from flask_cors import CORS
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import stripe
import threading
import time

from config import config
from models import db, bcrypt, User
from routes import register_blueprints

# Initialize Sentry for error tracking (production only)
SENTRY_DSN = os.getenv('SENTRY_DSN')
if SENTRY_DSN:
    import sentry_sdk
    from sentry_sdk.integrations.flask import FlaskIntegration
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[FlaskIntegration()],
        traces_sample_rate=0.1,  # 10% of transactions for performance
        profiles_sample_rate=0.1,
        environment=os.getenv('FLASK_ENV', 'production')
    )

# Initialize extensions globally
csrf = CSRFProtect()
limiter = Limiter(key_func=get_remote_address, default_limits=["200 per day", "50 per hour"])

def create_app(config_name=None):
    if config_name is None:
        config_name = os.getenv('FLASK_ENV', 'development')
        
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # Logging configuration
    configure_logging(app)
    
    # Initialize extensions
    CORS(app)
    db.init_app(app)
    bcrypt.init_app(app)
    csrf.init_app(app)
    limiter.init_app(app)
    migrate = Migrate(app, db)
    
    # Exempt API routes from CSRF (they use tokens)
    from routes.api import api_bp
    csrf.exempt(api_bp)
    
    # Exempt webhooks from CSRF (external services)
    from routes.webhooks import webhooks_bp
    csrf.exempt(webhooks_bp)
    
    # Login manager configuration
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message_category = 'info'
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    # Configure Stripe
    stripe.api_key = app.config.get('STRIPE_SECRET_KEY')
    
    # Register Blueprints
    register_blueprints(app)
    
    # Register Error Handlers
    register_error_handlers(app)
    
    app.logger.info(f'Application startup in {config_name} mode')
    
    # Keep-alive route for Render free tier
    @app.route('/ping')
    def ping():
        return jsonify({"status": "alive", "timestamp": time.time()}), 200

    # Start Marketing Scheduler in a background thread if enabled
    if os.getenv('ENABLE_SCHEDULER_THREAD') == 'true':
        from automation.scheduler import run_automation_cycle
        def run_scheduler_loop():
            interval = int(os.getenv('SCRAPE_INTERVAL_MINUTES', 30)) * 60
            app.logger.info(f"Starting background scheduler thread (Interval: {interval}s)")
            while True:
                try:
                    with app.app_context():
                        run_automation_cycle()
                except Exception as e:
                    app.logger.error(f"Scheduler thread error: {e}")
                time.sleep(interval)
        
        thread = threading.Thread(target=run_scheduler_loop, daemon=True)
        thread.start()
    
    return app


def configure_logging(app):
    """Configure logging for the application"""
    if not app.debug and not app.testing:
        if not os.path.exists('logs'):
            os.mkdir('logs')
            
        file_handler = RotatingFileHandler(
            'logs/leadfinder.log', maxBytes=10240, backupCount=10
        )
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        
        app.logger.setLevel(logging.INFO)


def register_error_handlers(app):
    """Register global error handlers"""
    
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template('errors/500.html'), 500


# Create the application instance
app = create_app()

# ============================================
# CLI COMMANDS
# ============================================

@app.cli.command('init-db')
def init_db():
    """Initialize the database"""
    db.create_all()
    print('Database initialized.')


@app.cli.command('seed-demo')
def seed_demo():
    """Seed demo data"""
    # Assuming seeder.py is in automation module and works with current context
    from automation.seeder import seed_demo_data
    seed_demo_data()
    print('Demo data seeded.')


if __name__ == '__main__':
    app.run()
