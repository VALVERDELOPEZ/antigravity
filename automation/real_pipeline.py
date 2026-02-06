"""
Lead Finder AI - Real Scraping Pipeline
Uses real APIs (Reddit, HackerNews, etc.) to find leads and score them with AI
"""
import os
import sys
import logging
from datetime import datetime
from typing import List

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv('.env.local')

from models import db, Lead, User
from automation.scraper import MultiPlatformScraper, RawLead
from automation.ai_generator import score_lead_with_ai

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("RealPipeline")


def is_real_scraping_available() -> bool:
    """Check if real scraping APIs are configured"""
    reddit_configured = bool(os.getenv('REDDIT_CLIENT_ID') and os.getenv('REDDIT_CLIENT_SECRET'))
    return reddit_configured


def run_real_pipeline(user_id: int, keywords: List[str], num_leads: int = 10) -> List[Lead]:
    """
    Run the REAL lead generation pipeline:
    1. Scrape from Reddit (and other platforms if configured)
    2. Score each lead with OpenAI
    3. Save to database with source_type='real'
    """
    logger.info(f"\n{'='*60}")
    logger.info(f"🔍 REAL SCRAPING PIPELINE - User ID: {user_id}")
    logger.info(f"{'='*60}")
    logger.info(f"Keywords: {keywords}")
    
    # Initialize scraper with real APIs
    scraper = MultiPlatformScraper(
        reddit_client_id=os.getenv('REDDIT_CLIENT_ID'),
        reddit_client_secret=os.getenv('REDDIT_CLIENT_SECRET'),
        reddit_user_agent=os.getenv('REDDIT_USER_AGENT', 'LeadFinderAI/1.0'),
        twitter_bearer_token=os.getenv('TWITTER_BEARER_TOKEN')
    )
    
    # Determine which platforms are available
    available_platforms = list(scraper.scrapers.keys())
    logger.info(f"Available platforms: {available_platforms}")
    
    if not available_platforms:
        logger.warning("No real scrapers available. Check your API keys.")
        return []
    
    # Scrape leads
    logger.info(f"Starting real scraping from: {available_platforms}")
    raw_leads = scraper.scrape_all(keywords, platforms=available_platforms, limit_per_platform=num_leads)
    
    if not raw_leads:
        logger.info("No leads found matching keywords")
        return []
    
    logger.info(f"Found {len(raw_leads)} raw leads, now scoring with AI...")
    
    created_leads = []
    openai_key = os.getenv('OPENAI_API_KEY')
    
    for raw_lead in raw_leads[:num_leads]:  # Limit to requested number
        try:
            # Score with AI if available
            if openai_key:
                lead_data = {
                    'platform': raw_lead.platform,
                    'username': raw_lead.username,
                    'title': raw_lead.title,
                    'content': raw_lead.content
                }
                score_data = score_lead_with_ai(lead_data)
            else:
                # Default scoring if no OpenAI
                score_data = {
                    'score': 5,
                    'urgency': 5,
                    'budget_indicator': 'medium',
                    'problem_summary': raw_lead.title[:200]
                }
            
            # Create lead in database
            lead = Lead(
                user_id=user_id,
                platform=raw_lead.platform,
                username=raw_lead.username,
                title=raw_lead.title,
                content=raw_lead.content,
                post_url=raw_lead.post_url,
                profile_url=raw_lead.profile_url,
                score=score_data.get('score', 5),
                urgency=score_data.get('urgency', 5),
                budget_indicator=score_data.get('budget_indicator', 'medium'),
                problem_summary=score_data.get('problem_summary', ''),
                source_created_at=raw_lead.source_created_at or datetime.utcnow(),
                source_type='real',  # REAL scraped lead
                status='new'
            )
            
            db.session.add(lead)
            created_leads.append(lead)
            logger.info(f"  ✓ {raw_lead.platform}: @{raw_lead.username} - Score: {score_data.get('score', 5)}/10")
            
        except Exception as e:
            logger.error(f"Error processing lead {raw_lead.username}: {e}")
            continue
    
    db.session.commit()
    
    # Update user stats
    user = User.query.get(user_id)
    if user:
        user.leads_found_count = (user.leads_found_count or 0) + len(created_leads)
        db.session.commit()
    
    logger.info(f"\n{'='*60}")
    logger.info(f"✅ REAL PIPELINE COMPLETE: Created {len(created_leads)} leads")
    logger.info(f"{'='*60}\n")
    
    return created_leads


if __name__ == "__main__":
    # Test the real pipeline
    from app import app
    
    with app.app_context():
        user = User.query.first()
        if user:
            keywords = ['looking for developer', 'need help with automation', 'recommendations for tools']
            run_real_pipeline(user.id, keywords, num_leads=5)
        else:
            print("No users found. Run 'flask seed-demo' first.")
