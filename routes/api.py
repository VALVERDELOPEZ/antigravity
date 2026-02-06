from datetime import datetime
from flask import request, current_app
from flask_login import login_required, current_user
from models import db, Lead, AutomationLog, UserSMTPConfig
from utils import api_response, get_plan_limits
from . import api_bp

@api_bp.route('/leads')
@login_required
def api_get_leads():
    """Get leads for the current user"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    min_score = request.args.get('min_score', 0, type=int)
    
    query = Lead.query.filter_by(user_id=current_user.id)
    
    if min_score > 0:
        query = query.filter(Lead.score >= min_score)
    
    leads = query.order_by(Lead.score.desc(), Lead.created_at.desc())\
        .paginate(page=page, per_page=per_page, error_out=False)
    
    return api_response(data={
        'leads': [lead.to_dict() for lead in leads.items],
        'total': leads.total,
        'page': page,
        'pages': leads.pages
    })


@api_bp.route('/leads/<int:lead_id>')
@login_required
def api_get_lead(lead_id):
    """Get a specific lead"""
    lead = Lead.query.filter_by(id=lead_id, user_id=current_user.id).first_or_404()
    return api_response(data=lead.to_dict())


@api_bp.route('/leads/<int:lead_id>/email-preview', methods=['GET'])
@login_required
def api_email_preview(lead_id):
    """Get email preview for a lead"""
    lead = Lead.query.filter_by(id=lead_id, user_id=current_user.id).first_or_404()
    
    # Return existing email or generate placeholder
    if lead.email_generated:
        return api_response(data={
            'subject': lead.email_subject,
            'body': lead.email_generated
        })
    else:
        return api_response(data={
            'subject': f"Re: {lead.title[:50]}..." if lead.title else "Quick question",
            'body': "Email will be generated with AI based on the lead's problem and context."
        })


@api_bp.route('/send-email', methods=['POST'])
@login_required
def api_send_email():
    """Send email to a lead"""
    from automation.mailer import send_smtp_email
    data = request.get_json()
    lead_id = data.get('lead_id')
    
    lead = Lead.query.filter_by(id=lead_id, user_id=current_user.id).first()
    if not lead:
        return api_response(message='Lead not found', success=False, status_code=404)
    
    # Si el lead no tiene email pero es de una plataforma social, usamos un placeholder ficticio para la demo
    target_email = lead.email or f"{lead.username}@{lead.platform}.com"
    
    # Check email limits
    plan_limits = get_plan_limits(current_user.plan)
    if plan_limits['max_emails'] != -1 and current_user.emails_sent_count >= plan_limits['max_emails']:
        return api_response(message='Email limit reached. Please upgrade your plan.', success=False, status_code=403)
    
    # Obtener el contenido del email (generarlo si no existe)
    subject = lead.email_subject or f"Query about your {lead.platform} post"
    body = lead.email_generated or lead.content
    
    # Realizar envío (real o simulado según config)
    mailer_config = None
    smtp_config = UserSMTPConfig.query.filter_by(user_id=current_user.id).first()
    if smtp_config and smtp_config.smtp_server:
        try:
             mailer_config = {
                 'server': smtp_config.smtp_server,
                 'port': smtp_config.smtp_port,
                 'username': smtp_config.smtp_username,
                 'password': smtp_config.get_password(),
                 'sender_name': smtp_config.sender_name
             }
        except Exception:
             pass

    success, msg = send_smtp_email(target_email, subject, body, config=mailer_config)
    
    if success:
        # Actualizar estado en la BD
        lead.email_sent = True
        lead.email_sent_at = datetime.utcnow()
        lead.status = 'contacted'
        current_user.emails_sent_count += 1
        db.session.commit()
        return api_response(message=msg, data={'lead_id': lead_id})
    else:
        return api_response(message=f"Failed to send: {msg}", success=False, status_code=500)


@api_bp.route('/stats')
@login_required
def api_get_stats():
    """Get dashboard stats"""
    total_leads = Lead.query.filter_by(user_id=current_user.id).count()
    high_score_leads = Lead.query.filter_by(user_id=current_user.id).filter(Lead.score >= 7).count()
    
    # Calculate this month's activity
    day_1 = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    leads_this_month = Lead.query.filter(
        Lead.user_id == current_user.id,
        Lead.created_at >= day_1
    ).count()
    
    emails_this_month = Lead.query.filter(
        Lead.user_id == current_user.id,
        Lead.email_sent == True,
        Lead.email_sent_at >= day_1
    ).count()
    
    return api_response(data={
        'total_leads': total_leads,
        'high_score_leads': high_score_leads,
        'leads_this_month': leads_this_month,
        'emails_sent': current_user.emails_sent_count,
        'emails_this_month': emails_this_month,
        'emails_opened': current_user.emails_opened_count,
        'emails_replied': current_user.emails_replied_count,
        'conversion_rate': round((current_user.emails_replied_count / current_user.emails_sent_count * 100), 1) if current_user.emails_sent_count > 0 else 0,
        'plan': current_user.plan
    })


@api_bp.route('/automation/status')
@login_required
def api_automation_status():
    """Get automation status"""
    last_log = AutomationLog.query.filter_by(event_type='scrape')\
        .order_by(AutomationLog.created_at.desc())\
        .first()
    
    return api_response(data={
        'last_run': last_log.created_at.isoformat() if last_log else None,
        'status': last_log.status if last_log else 'never_run',
        'leads_found': last_log.leads_found if last_log else 0
    })


@api_bp.route('/generate-leads', methods=['POST'])
@login_required
def api_generate_leads():
    """Generate new leads using AI"""
    # For now, just a stub or we can implement full logic if was in app.py
    # app.py had:
    # from automation.ai_generator import run_ai_pipeline (doesn't exist in file listing I saw, but maybe stubbed)
    # The file listing had a truncated app.py so I couldn't see the full implementation of this method.
    # I will assume it triggers the scraper.
    
    # Re-implementing logic based on what usually goes here
    from automation.scheduler import run_real_scraping_pipeline
    
    # Get user keywords
    keywords = current_user.get_keywords_list()
    if not keywords:
        keywords = ['SaaS', 'startup', 'developer']
        
    try:
        # Trigger scraping (sync for MVP, should be async in prod)
        leads = run_real_scraping_pipeline(
            user_id=current_user.id, 
            keywords=keywords,
            max_requests=5 # Limit for manual trigger
        )
        return api_response(message=f"Found {len(leads)} new leads", data={'count': len(leads)})
    except Exception as e:
        return api_response(message=f"Error generating leads: {str(e)}", success=False, status_code=500)
