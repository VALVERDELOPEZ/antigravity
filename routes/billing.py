import stripe
from flask import render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from models import db, User, Transaction
from utils import api_response
from . import billing_bp

@billing_bp.route('/checkout/<plan>')
@login_required
def checkout(plan):
    """Checkout page for subscription"""
    if plan not in ['starter', 'pro']:
        flash('Invalid plan selected.', 'error')
        return redirect(url_for('public.pricing'))
    
    plan_prices = {
        'starter': {'price': 49, 'stripe_price': current_app.config.get('STRIPE_PRICE_STARTER')},
        'pro': {'price': 99, 'stripe_price': current_app.config.get('STRIPE_PRICE_PRO')}
    }
    
    return render_template('billing/checkout.html',
        plan=plan,
        plan_info=plan_prices[plan],
        stripe_key=current_app.config.get('STRIPE_PUBLISHABLE_KEY')
    )


@billing_bp.route('/api/create-checkout-session', methods=['POST'])
@login_required
def create_checkout_session():
    """Create Stripe checkout session"""
    data = request.get_json()
    plan = data.get('plan')
    
    price_ids = {
        'starter': current_app.config.get('STRIPE_PRICE_STARTER'),
        'pro': current_app.config.get('STRIPE_PRICE_PRO')
    }
    
    if plan not in price_ids or not price_ids[plan]:
        return api_response(message='Invalid plan', success=False, status_code=400)
    
    try:
        # Create or get Stripe customer
        if not current_user.stripe_customer_id:
            customer = stripe.Customer.create(
                email=current_user.email,
                name=current_user.name,
                metadata={'user_id': current_user.id}
            )
            current_user.stripe_customer_id = customer.id
            db.session.commit()
        
        # Create checkout session
        session = stripe.checkout.Session.create(
            customer=current_user.stripe_customer_id,
            payment_method_types=['card'],
            line_items=[{
                'price': price_ids[plan],
                'quantity': 1
            }],
            mode='subscription',
            success_url=f"{current_app.config['APP_URL']}/billing/success?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{current_app.config['APP_URL']}/pricing",
            metadata={
                'user_id': current_user.id,
                'plan': plan
            }
        )
        
        return api_response(data={'sessionId': session.id})
    
    except stripe.error.StripeError as e:
        return api_response(message=str(e), success=False, status_code=400)


@billing_bp.route('/billing/success')
@login_required
def billing_success():
    """Billing success page"""
    session_id = request.args.get('session_id')
    return render_template('billing/success.html', session_id=session_id)


@billing_bp.route('/billing/history')
@login_required
def billing_history():
    """Payment history"""
    transactions = Transaction.query.filter_by(user_id=current_user.id)\
        .order_by(Transaction.created_at.desc())\
        .all()
    return render_template('billing/history.html', transactions=transactions)
