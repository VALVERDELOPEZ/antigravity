from datetime import datetime, timedelta
from flask import render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from sqlalchemy import func
from models import db, Lead, UserKeywords, UserSMTPConfig
from utils import get_plan_limits
from . import dashboard_bp

@dashboard_bp.route('/dashboard')
@login_required
def dashboard():
    """Main dashboard"""
    # Get stats
    total_leads = Lead.query.filter_by(user_id=current_user.id).count()
    high_score_leads = Lead.query.filter_by(user_id=current_user.id).filter(Lead.score >= 7).count()
    emails_sent = current_user.emails_sent_count
    emails_replied = current_user.emails_replied_count
    
    # Calculate conversion rate
    conversion_rate = (emails_replied / emails_sent * 100) if emails_sent > 0 else 0
    
    # Get recent leads
    recent_leads = Lead.query.filter_by(user_id=current_user.id)\
        .order_by(Lead.created_at.desc())\
        .limit(10)\
        .all()
    
    # Get plan limits
    plan_limits = get_plan_limits(current_user.plan)
    
    return render_template('dashboard/index.html',
        total_leads=total_leads,
        high_score_leads=high_score_leads,
        emails_sent=emails_sent,
        emails_replied=emails_replied,
        conversion_rate=round(conversion_rate, 1),
        recent_leads=recent_leads,
        plan_limits=plan_limits
    )


@dashboard_bp.route('/dashboard/leads')
@login_required
def leads():
    """Leads management page"""
    page = request.args.get('page', 1, type=int)
    per_page = 25
    
    # Filters
    platform = request.args.get('platform')
    language = request.args.get('language')  # New language filter
    min_score = request.args.get('min_score', type=int)
    status = request.args.get('status')
    search = request.args.get('search', '')
    
    query = Lead.query.filter_by(user_id=current_user.id)
    
    if platform:
        query = query.filter_by(platform=platform)
    if language:
        query = query.filter_by(language=language)
    if min_score:
        query = query.filter(Lead.score >= min_score)
    if status:
        query = query.filter_by(status=status)
    if search:
        query = query.filter(
            (Lead.title.ilike(f'%{search}%')) | 
            (Lead.content.ilike(f'%{search}%')) |
            (Lead.username.ilike(f'%{search}%'))
        )
    
    leads_pagination = query.order_by(Lead.score.desc(), Lead.created_at.desc())\
        .paginate(page=page, per_page=per_page, error_out=False)
    
    return render_template('dashboard/leads.html',
        leads=leads_pagination.items,
        pagination=leads_pagination
    )


@dashboard_bp.route('/dashboard/analytics')
@login_required
def analytics():
    """Analytics page"""
    # Get lead stats by platform
    leads_by_platform_rows = db.session.query(
        Lead.platform,
        func.count(Lead.id).label('count')
    ).filter_by(user_id=current_user.id)\
    .group_by(Lead.platform)\
    .all()
    # Convert to list of dicts for JSON serialization
    leads_by_platform = [{'platform': row.platform, 'count': row.count} for row in leads_by_platform_rows]
    
    # Get score distribution
    score_distribution_rows = db.session.query(
        Lead.score,
        func.count(Lead.id).label('count')
    ).filter_by(user_id=current_user.id)\
    .group_by(Lead.score)\
    .order_by(Lead.score)\
    .all()
    score_distribution = [{'score': row.score, 'count': row.count} for row in score_distribution_rows]
    
    # Get email stats over time
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    
    email_stats_rows = db.session.query(
        func.date(Lead.email_sent_at).label('date'),
        func.count(Lead.id).label('sent'),
        func.sum(Lead.email_opened.cast(db.Integer)).label('opened'),
        func.sum(Lead.email_replied.cast(db.Integer)).label('replied')
    ).filter(
        Lead.user_id == current_user.id,
        Lead.email_sent == True,
        Lead.email_sent_at >= thirty_days_ago
    ).group_by(func.date(Lead.email_sent_at))\
    .order_by(func.date(Lead.email_sent_at))\
    .all()
    email_stats = [{'date': str(row.date), 'sent': row.sent, 'opened': row.opened or 0, 'replied': row.replied or 0} for row in email_stats_rows]
    
    return render_template('dashboard/analytics.html',
        leads_by_platform=leads_by_platform,
        score_distribution=score_distribution,
        email_stats=email_stats
    )


@dashboard_bp.route('/dashboard/settings', methods=['GET', 'POST'])
@login_required
def settings():
    """User settings page"""
    # Get or create user keywords config
    user_config = UserKeywords.query.filter_by(user_id=current_user.id).first()
    if not user_config:
        user_config = UserKeywords(user_id=current_user.id)
        db.session.add(user_config)
        db.session.commit()

    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'update_profile':
            current_user.name = request.form.get('name', '').strip()
            flash('Profile updated successfully.', 'success')
        
        elif action == 'update_search':
            # Keywords (textarea, one per line or comma separated)
            raw_keywords = request.form.get('keywords', '')
            # Normalizar: dividir por saltos de línea y limpiar, permitir comas también
            keywords_list = [k.strip() for k in raw_keywords.replace(',', '\n').split('\n') if k.strip()]
            
            # Subreddits (comma separated)
            raw_subreddits = request.form.get('subreddits', '')
            subreddits_list = [s.strip() for s in raw_subreddits.split(',') if s.strip()]
            
            # Languages (checkboxes)
            languages = request.form.getlist('languages')
            if not languages: languages = ['en']
            
            # Platforms (checkboxes)
            platforms = request.form.getlist('platforms')
            
            # Min Score
            try:
                min_score = int(request.form.get('min_score', 7))
            except ValueError:
                min_score = 7
            
            # Update UserKeywords
            user_config.keywords = keywords_list
            user_config.subreddits = subreddits_list
            user_config.languages = languages
            user_config.active_platforms = platforms
            user_config.min_score = min_score
            
            # Update legacy fields for compatibility
            current_user.keywords = ','.join(keywords_list)
            current_user.platforms = ','.join(platforms)
            
            flash('Search settings updated successfully.', 'success')
        
        elif action == 'update_email_config':
            # Get or create SMTP config
            smtp_config = UserSMTPConfig.query.filter_by(user_id=current_user.id).first()
            if not smtp_config:
                smtp_config = UserSMTPConfig(user_id=current_user.id)
                db.session.add(smtp_config)
            
            smtp_config.sender_name = request.form.get('sender_name', '')
            smtp_config.smtp_server = request.form.get('smtp_server', '')
            try:
                smtp_config.smtp_port = int(request.form.get('smtp_port', 587))
            except ValueError:
                smtp_config.smtp_port = 587
            smtp_config.smtp_username = request.form.get('smtp_username', '')
            
            new_password = request.form.get('smtp_password', '')
            if new_password and new_password != '********':
                smtp_config.set_password(new_password)
            
            current_user.email_signature = request.form.get('email_signature', '')
            
            # Commit first
            db.session.commit()
            
            if request.form.get('test_connection'):
                try:
                    import smtplib
                    server = smtplib.SMTP(smtp_config.smtp_server, smtp_config.smtp_port, timeout=10)
                    server.starttls()
                    server.login(smtp_config.smtp_username, smtp_config.get_password())
                    server.quit()
                    flash('Connection successful! SMTP settings are valid.', 'success')
                except Exception as e:
                    flash(f'Connection failed: {str(e)}', 'error')
            else:
                flash('Email configuration saved successfully.', 'success')
        
        elif action == 'change_password':
            current_password = request.form.get('current_password')
            new_password = request.form.get('new_password')
            
            if not current_user.check_password(current_password):
                flash('Current password is incorrect.', 'error')
            elif len(new_password) < 8:
                flash('New password must be at least 8 characters.', 'error')
            else:
                current_user.set_password(new_password)
                flash('Password changed successfully.', 'success')
        
        db.session.commit()
        return redirect(url_for('dashboard.settings'))
    
    # SMTP Config
    smtp_config = UserSMTPConfig.query.filter_by(user_id=current_user.id).first()
    if not smtp_config:
        smtp_config = UserSMTPConfig(user_id=current_user.id) 
        
    plan_limits = get_plan_limits(current_user.plan)
    return render_template('dashboard/settings.html', 
                           plan_limits=plan_limits, 
                           user_config=user_config,
                           smtp_config=smtp_config)
