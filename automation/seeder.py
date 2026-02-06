"""
Lead Finder AI - Demo Data Seeder
Creates sample data for testing and demonstration
"""
import random
from datetime import datetime, timedelta

def seed_demo_data():
    """Seed the database with demo data"""
    from models import db, User, Lead, Transaction, AutomationLog
    
    # Create demo user
    demo_user = User.query.filter_by(email='demo@leadfinderai.com').first()
    if not demo_user:
        demo_user = User(
            email='demo@leadfinderai.com',
            name='Demo User',
            plan='pro',
            subscription_status='active',
            leads_found_count=156,
            emails_sent_count=45,
            emails_opened_count=28,
            emails_replied_count=8,
            keywords='looking for developer, need automation, struggling with leads, help with marketing',
            platforms='reddit,twitter,hackernews'
        )
        demo_user.set_password('demo123456')
        db.session.add(demo_user)
        db.session.commit()
    
    # Sample leads data
    sample_leads = [
        {'platform': 'reddit', 'username': 'startup_founder_23', 'title': 'Need help automating my lead generation process', 
         'content': 'Running a B2B SaaS and spending 4+ hours daily on manual lead gen. Looking for tools under $200/month.',
         'score': 9, 'urgency': 9, 'budget': 'high'},
        {'platform': 'twitter', 'username': 'growth_hacker_mike', 'title': 'Tweet about lead gen struggles',
         'content': 'Tired of cold outreach that gets 0.1% response rates. There has to be a better way!',
         'score': 8, 'urgency': 7, 'budget': 'medium'},
        {'platform': 'hackernews', 'username': 'techfounder', 'title': 'Show HN: Built an MVP, now need customers',
         'content': 'Launched my product but struggling to find B2B leads. Any automation recommendations?',
         'score': 8, 'urgency': 8, 'budget': 'medium'},
        {'platform': 'reddit', 'username': 'agency_owner', 'title': 'How do you find clients for your agency?',
         'content': 'Marketing agency here. Our pipeline is empty. Need to automate prospecting ASAP.',
         'score': 9, 'urgency': 10, 'budget': 'high'},
        {'platform': 'indiehackers', 'username': 'solopreneur_jane', 'title': 'Lead gen for indie hackers',
         'content': 'Looking for affordable ways to find my first 100 customers. Budget around $50-100/month.',
         'score': 7, 'urgency': 6, 'budget': 'medium'},
    ]
    
    # Create leads
    for i, lead_data in enumerate(sample_leads):
        existing = Lead.query.filter_by(user_id=demo_user.id, username=lead_data['username']).first()
        if not existing:
            lead = Lead(
                user_id=demo_user.id,
                platform=lead_data['platform'],
                username=lead_data['username'],
                title=lead_data['title'],
                content=lead_data['content'],
                post_url=f"https://{lead_data['platform']}.com/post/{i}",
                score=lead_data['score'],
                urgency=lead_data['urgency'],
                budget_indicator=lead_data['budget'],
                problem_summary=lead_data['title'],
                source_type='demo',  # Mark as demo data
                created_at=datetime.utcnow() - timedelta(hours=random.randint(1, 72))
            )
            db.session.add(lead)
    
    db.session.commit()
    print(f"Demo data seeded for user: {demo_user.email}")
