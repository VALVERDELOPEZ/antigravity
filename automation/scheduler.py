"""
Lead Finder AI - Production Scheduler
======================================
Runs the scraping pipeline on a configurable interval.
Supports both minute-based (MVP) and hour-based (production) intervals.

Usage:
    python automation/scheduler.py

Environment Variables:
    SCRAPE_INTERVAL_MINUTES=30  # Run every 30 minutes (MVP mode)
    SCRAPE_INTERVAL_HOURS=8     # Run every 8 hours (production mode)
    MIN_ENGAGEMENT_SCORE=2      # Minimum upvotes+comments to keep lead
    MAX_REQUESTS_PER_CYCLE=20   # Limit requests per cycle (rate limiting)
"""
import os
import sys
import logging
import time
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv('.env.local')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("Scheduler")


def check_configuration() -> dict:
    """
    Check which APIs and services are configured.
    Returns a dict with configuration status.
    """
    config = {
        'openai': bool(os.getenv('OPENAI_API_KEY')),
        'database': 'postgresql' if 'postgresql' in os.getenv('DATABASE_URL', '') else 'sqlite',
        'smtp': bool(os.getenv('SMTP_SERVER') and os.getenv('SMTP_USERNAME')),
        'interval_minutes': int(os.getenv('SCRAPE_INTERVAL_MINUTES', 30)),
        'min_engagement': int(os.getenv('MIN_ENGAGEMENT_SCORE', 2)),
        'max_requests': int(os.getenv('MAX_REQUESTS_PER_CYCLE', 20)),
    }
    
    logger.info("=" * 60)
    logger.info("CONFIGURATION STATUS")
    logger.info("=" * 60)
    logger.info(f"  Database:        {config['database'].upper()}")
    logger.info(f"  OpenAI API:      {'✓ Configured' if config['openai'] else '✗ Not configured'}")
    logger.info(f"  SMTP Email:      {'✓ Configured' if config['smtp'] else '✗ Not configured'}")
    logger.info(f"  Interval:        Every {config['interval_minutes']} minutes")
    logger.info(f"  Min engagement:  {config['min_engagement']} (upvotes+comments)")
    logger.info(f"  Max requests:    {config['max_requests']} per cycle")
    logger.info("=" * 60)
    
    return config


def get_user_keywords(user) -> list:
    """
    Get keywords from user configuration.
    Falls back to defaults if none configured.
    """
    if user.keywords:
        keywords = [k.strip() for k in user.keywords.split(',') if k.strip()]
        if keywords:
            return keywords
    
    # Default keywords for lead generation
    return [
        'looking for developer',
        'need help with',
        'struggling with',
        'recommendations for',
        'automation',
        'SaaS',
        'startup',
        "how do I",
    ]


def run_real_scraping_pipeline(user_id: int, keywords: list, 
                                min_engagement: int = 2, 
                                max_requests: int = 20,
                                languages: list = None,
                                platforms: list = None) -> list:
    """
    Run the real scraping pipeline for a user with multi-language support.
    
    1. Scrape Reddit (EN, ES, PT, FR), HN, Indie Hackers
    2. Filter by keywords and engagement
    3. Score with AI (if OpenAI configured)
    4. Save to database with language tracking
    
    Args:
        user_id: Database user ID
        keywords: Keywords to search for
        min_engagement: Minimum engagement score
        max_requests: Max HTTP requests
        languages: Languages to scrape (default: all - en, es, pt, fr)
    
    Returns list of created Lead objects.
    """
    from models import db, Lead, User
    from automation.scraper import MultiPlatformScraper, SUBREDDITS_BY_LANGUAGE
    
    # Default to all configured languages
    langs_to_scrape = languages or list(SUBREDDITS_BY_LANGUAGE.keys())
    
    logger.info(f"Starting MULTI-LANGUAGE scraping pipeline for user {user_id}")
    logger.info(f"Languages: {', '.join(langs_to_scrape)}")
    
    # Initialize scraper
    scraper = MultiPlatformScraper(
        min_engagement=min_engagement,
        max_requests=max_requests
    )
    
    # Determine platforms to scrape
    platforms_to_scrape = platforms or ['reddit', 'hackernews', 'indiehackers']
    
    # Scrape all platforms with multi-language support
    raw_leads = scraper.scrape_all_multilang(
        platforms=platforms_to_scrape,
        languages=langs_to_scrape,
        limit_per_platform=10
    )
    
    if not raw_leads:
        logger.warning("No leads found from scraping")
        return []
    
    logger.info(f"Found {len(raw_leads)} raw leads, now processing...")
    
    # Count by language
    lang_counts = {}
    for raw in raw_leads:
        lang_counts[raw.language] = lang_counts.get(raw.language, 0) + 1
    logger.info(f"Leads by language: {lang_counts}")
    
    # Check for existing leads to avoid duplicates
    created_leads = []
    
    for raw in raw_leads:
        # Check if lead already exists by external_id or post_url
        existing = Lead.query.filter(
            Lead.user_id == user_id,
            (Lead.external_id == raw.external_id) | (Lead.post_url == raw.post_url)
        ).first()
        
        if existing:
            logger.debug(f"Skipping duplicate: {raw.title[:50]}")
            continue
        
        # Create new lead with language tracking
        lead = Lead(
            user_id=user_id,
            username=raw.username,
            platform=raw.platform,
            title=raw.title,
            content=raw.content,
            post_url=raw.post_url,
            profile_url=raw.profile_url,
            external_id=raw.external_id,
            source=raw.source,
            language=raw.language,  # Track source language
            source_type='real',  # Mark as real scraped data
            source_created_at=raw.source_created_at,
            status='new',
            score=min(10, max(1, raw.engagement_score // 5 + 5)),  # Basic score from engagement
        )
        
        db.session.add(lead)
        created_leads.append(lead)
    
    # Commit all new leads
    if created_leads:
        db.session.commit()
        logger.info(f"Saved {len(created_leads)} new leads to database")
        
        # Log by language
        saved_langs = {}
        for lead in created_leads:
            saved_langs[lead.language] = saved_langs.get(lead.language, 0) + 1
        logger.info(f"Saved by language: {saved_langs}")
        
        # Update user stats
        user = User.query.get(user_id)
        if user:
            user.leads_found_count += len(created_leads)
            db.session.commit()
    
    return created_leads


def run_ai_scoring(leads: list) -> None:
    """
    Score leads using AI if OpenAI is configured.
    Updates lead.score, lead.urgency, lead.problem_summary in place.
    """
    openai_key = os.getenv('OPENAI_API_KEY')
    if not openai_key:
        logger.warning("OpenAI not configured, skipping AI scoring")
        return
    
    try:
        from automation.qualifier import LeadQualifier
        from models import db
        
        qualifier = LeadQualifier(api_key=openai_key)
        
        for lead in leads:
            try:
                result = qualifier.qualify_lead({
                    'title': lead.title,
                    'content': lead.content,
                    'platform': lead.platform,
                    'username': lead.username,
                })
                
                if result:
                    lead.score = result.get('score', lead.score)
                    lead.urgency = result.get('urgency', 5)
                    lead.problem_summary = result.get('problem_summary', '')
                    lead.budget_indicator = result.get('budget_indicator', 'medium')
                    
            except Exception as e:
                logger.error(f"Error scoring lead {lead.id}: {e}")
                continue
        
        db.session.commit()
        logger.info(f"AI scoring completed for {len(leads)} leads")
        
    except ImportError:
        logger.warning("Qualifier module not available, skipping AI scoring")
    except Exception as e:
        logger.error(f"Error in AI scoring: {e}")


def run_automation_cycle():
    """
    Run one complete automation cycle:
    1. Get all users with paid plans
    2. For each user, run scraping based on their keywords
    3. Score leads with AI
    4. Log results
    """
    from app import app
    from models import db, User, AutomationLog
    
    with app.app_context():
        config = check_configuration()
        
        # Get users who should receive automated leads
        # For MVP, also include 'free' users who are the demo user
        users = User.query.filter(
            (User.plan.in_(['starter', 'pro', 'enterprise'])) | 
            (User.email == 'demo@leadfinderai.com')
        ).all()
        
        if not users:
            logger.info("No users found for automation. Skipping cycle.")
            return
        
        total_leads = 0
        
        for user in users:
            try:
                logger.info(f"\n{'='*50}")
                logger.info(f"Processing user: {user.email} (Plan: {user.plan})")
                logger.info(f"{'='*50}")
                
                from models import UserKeywords
                
                # Get keywords and config
                user_config = UserKeywords.query.filter_by(user_id=user.id).first()
                
                if user_config and user_config.keywords:
                    keywords = user_config.keywords
                    languages = user_config.languages or ['en']
                    platforms = user_config.active_platforms or ['reddit', 'hn', 'indie_hackers']
                    logger.info(f"Using CUSTOM config for {user.email}")
                else:
                    keywords = get_user_keywords(user)
                    languages = ['en']
                    platforms = ['reddit', 'hn', 'indie_hackers']
                    logger.info(f"Using DEFAULT config for {user.email}")

                logger.info(f"Keywords: {keywords[:3]}...")
                
                # Run real scraping pipeline
                leads = run_real_scraping_pipeline(
                    user_id=user.id,
                    keywords=keywords,
                    min_engagement=config['min_engagement'],
                    max_requests=config['max_requests'],
                    languages=languages,
                    platforms=platforms
                )
                
                leads_created = len(leads)
                total_leads += leads_created
                
                # Score with AI if we have new leads
                if leads and config['openai']:
                    run_ai_scoring(leads)
                
                # 5. Run outreach if enabled
                if leads and os.getenv('ENABLE_AUTONOMOUS_OUTREACH') == 'true':
                    try:
                        from automation.outreach_agent import OutreachAgent
                        agent = OutreachAgent(app.app_context())
                        sent_count = agent.process_outreach_cycle(limit=5)
                        logger.info(f"✓ Outreach cycle: {sent_count} emails sent")
                    except Exception as e:
                        logger.error(f"Error in outreach cycle: {e}")

                # Log the automation run
                log = AutomationLog(
                    event_type='scrape',
                    platform='multi',
                    status='success' if leads_created > 0 else 'no_new_leads',
                    leads_found=leads_created,
                    message=f"Real scraping: {leads_created} new leads"
                )
                db.session.add(log)
                db.session.commit()
                
                logger.info(f"✓ User {user.email}: {leads_created} new leads")
                
            except Exception as e:
                logger.error(f"Error processing user {user.email}: {str(e)}")
                db.session.rollback()
                
                # Log error
                try:
                    log = AutomationLog(
                        event_type='scrape',
                        platform='multi',
                        status='error',
                        error_message=str(e)[:500]
                    )
                    db.session.add(log)
                    db.session.commit()
                except Exception:
                    pass
        
        logger.info(f"\n{'='*50}")
        logger.info(f"CYCLE COMPLETE: {total_leads} total new leads")
        logger.info(f"{'='*50}\n")


def start_scheduler():
    """
    Main entry point for the scheduler.
    Runs automation on a configurable interval.
    """
    interval_minutes = int(os.getenv('SCRAPE_INTERVAL_MINUTES', 30))
    interval_seconds = interval_minutes * 60
    
    logger.info("\n" + "=" * 60)
    logger.info("  LEAD FINDER AI - REAL SCRAPING SCHEDULER")
    logger.info("=" * 60)
    logger.info(f"  Mode:     PRODUCTION (Real Scraping)")
    logger.info(f"  Interval: Every {interval_minutes} minutes")
    logger.info(f"  Sources:  Reddit JSON, Hacker News, Indie Hackers")
    logger.info("=" * 60 + "\n")
    
    # Run immediately on start
    logger.info("Running initial cycle...")
    run_automation_cycle()
    
    # Then run on schedule
    while True:
        try:
            next_run = datetime.now().timestamp() + interval_seconds
            next_run_str = datetime.fromtimestamp(next_run).strftime('%Y-%m-%d %H:%M:%S')
            logger.info(f"\nNext run at: {next_run_str}")
            logger.info(f"Sleeping for {interval_minutes} minutes...")
            
            time.sleep(interval_seconds)
            run_automation_cycle()
            
        except KeyboardInterrupt:
            logger.info("\nScheduler stopped by user (Ctrl+C)")
            break
        except Exception as e:
            logger.error(f"Scheduler error: {str(e)}")
            logger.info("Waiting 60 seconds before retry...")
            time.sleep(60)


def run_once():
    """
    Run a single automation cycle and exit.
    Useful for testing or one-off runs.
    """
    logger.info("Running single automation cycle...")
    run_automation_cycle()
    logger.info("Done!")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Lead Finder AI Scheduler')
    parser.add_argument('--once', action='store_true', 
                        help='Run once and exit (instead of continuous loop)')
    args = parser.parse_args()
    
    if args.once:
        run_once()
    else:
        start_scheduler()
