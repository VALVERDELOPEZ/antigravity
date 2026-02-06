from flask import Blueprint

# Define Blueprints
public_bp = Blueprint('public', __name__)
auth_bp = Blueprint('auth', __name__)
dashboard_bp = Blueprint('dashboard', __name__)
api_bp = Blueprint('api', __name__)
billing_bp = Blueprint('billing', __name__)
webhooks_bp = Blueprint('webhooks', __name__)

def register_blueprints(app):
    """Register all blueprints to the app"""
    from routes.public import public_bp
    from routes.auth import auth_bp
    from routes.dashboard import dashboard_bp
    from routes.api import api_bp
    from routes.billing import billing_bp
    from routes.webhooks import webhooks_bp

    app.register_blueprint(public_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(billing_bp)
    app.register_blueprint(webhooks_bp)
