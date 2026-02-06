import stripe
from flask import request, current_app
from models import db, User, Transaction, AutomationLog
from utils import api_response
from . import webhooks_bp

@webhooks_bp.route('/webhook/stripe', methods=['POST'])
def stripe_webhook():
    """Handle Stripe webhooks"""
    payload = request.data
    sig_header = request.headers.get('Stripe-Signature')
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, current_app.config.get('STRIPE_WEBHOOK_SECRET')
        )
    except ValueError:
        return 'Invalid payload', 400
    except stripe.error.SignatureVerificationError:
        return 'Invalid signature', 400
    
    # Handle events
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        user_id = session['metadata'].get('user_id')
        plan = session['metadata'].get('plan')
        
        if user_id and plan:
            user = User.query.get(user_id)
            if user:
                user.plan = plan
                user.stripe_subscription_id = session.get('subscription')
                user.subscription_status = 'active'
                
                # Create transaction record
                transaction = Transaction(
                    user_id=user.id,
                    stripe_payment_intent_id=session.get('payment_intent'),
                    type='subscription',
                    plan=plan,
                    amount=49 if plan == 'starter' else 99,
                    status='succeeded'
                )
                db.session.add(transaction)
                db.session.commit()
    
    elif event['type'] == 'customer.subscription.deleted':
        subscription = event['data']['object']
        user = User.query.filter_by(stripe_subscription_id=subscription['id']).first()
        if user:
            user.plan = 'free'
            user.subscription_status = 'canceled'
            db.session.commit()
    
    elif event['type'] == 'invoice.payment_failed':
        invoice = event['data']['object']
        customer_id = invoice.get('customer')
        user = User.query.filter_by(stripe_customer_id=customer_id).first()
        if user:
            user.subscription_status = 'past_due'
            db.session.commit()
    
    return 'OK', 200


@webhooks_bp.route('/webhook/signup', methods=['POST'])
def webhook_signup():
    """Webhook for new user signup notifications"""
    data = request.get_json()
    # Log new signup
    log = AutomationLog(
        event_type='signup',
        status='success',
        message=f"New user signed up: {data.get('email')}"
    )
    db.session.add(log)
    db.session.commit()
    return api_response(message='Signup logged')
