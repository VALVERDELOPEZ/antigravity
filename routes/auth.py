from datetime import datetime
from flask import render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from models import db, User, UserKeywords
from . import auth_bp

@auth_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    """User registration"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.dashboard'))
    
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        name = request.form.get('name', '').strip()
        plan = request.form.get('plan', 'free')
        
        # Validation
        if not email or not password:
            flash('Email and password are required.', 'error')
            return render_template('auth/signup.html')
        
        if len(password) < 8:
            flash('Password must be at least 8 characters.', 'error')
            return render_template('auth/signup.html')
        
        if User.query.filter_by(email=email).first():
            flash('Email already registered.', 'error')
            return render_template('auth/signup.html')
        
        # Create user
        user = User(email=email, name=name, plan=plan)
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        # Log in the user
        login_user(user)
        
        flash('Welcome to Lead Finder AI!', 'success')
        
        # Redirect to payment if paid plan selected
        if plan in ['starter', 'pro']:
            return redirect(url_for('billing.checkout', plan=plan))
        
        return redirect(url_for('auth.onboarding'))
    
    return render_template('auth/signup.html')


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.dashboard'))
    
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        remember = request.form.get('remember', False)
        
        user = User.query.filter_by(email=email).first()
        
        if user and user.check_password(password):
            user.last_login_at = datetime.utcnow()
            db.session.commit()
            
            login_user(user, remember=remember)
            
            if not user.onboarding_completed:
                return redirect(url_for('auth.onboarding'))
            
            next_page = request.args.get('next')
            return redirect(next_page or url_for('dashboard.dashboard'))
        
        flash('Invalid email or password.', 'error')
    
    return render_template('auth/login.html')


@auth_bp.route('/logout')
@login_required
def logout():
    """User logout"""
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('public.landing'))


@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    """Password reset request"""
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        # Check if user exists but don't reveal it
        user = User.query.filter_by(email=email).first()
        
        # Always show success message for security
        flash('If an account exists with this email, you will receive a password reset link.', 'info')
        
        # TODO: Send password reset email
        
        return redirect(url_for('auth.login'))
    
    return render_template('auth/forgot_password.html')


@auth_bp.route('/onboarding', methods=['GET', 'POST'])
@login_required
def onboarding():
    """User onboarding wizard"""
    if current_user.onboarding_completed:
        return redirect(url_for('dashboard.dashboard'))
        
    if request.method == 'POST':
        # 1. Process Keywords
        raw_keywords = request.form.get('keywords', '')
        keywords_list = [k.strip() for k in raw_keywords.replace(',', '\n').split('\n') if k.strip()]
        
        # 2. Process Languages
        languages = request.form.getlist('languages')
        if not languages: languages = ['en']
        
        # 3. Create/Update UserKeywords
        user_config = UserKeywords.query.filter_by(user_id=current_user.id).first()
        if not user_config:
            user_config = UserKeywords(user_id=current_user.id)
            db.session.add(user_config)
        
        user_config.keywords = keywords_list
        user_config.languages = languages
        # Defaults for onboarding
        user_config.active_platforms = ['reddit', 'hn', 'indie_hackers']
        user_config.min_score = 7
        
        # 4. Mark onboarding as complete
        current_user.onboarding_completed = True
        
        # Compatibility legacy fields
        current_user.keywords = ','.join(keywords_list)
        
        db.session.commit()
        
        flash('Welcome aboard! We are starting to find leads for you. Check back in a few minutes.', 'success')
        return redirect(url_for('dashboard.dashboard'))
        
    return render_template('onboarding.html')
