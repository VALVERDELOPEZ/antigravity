"""
Lead Finder AI - Autonomous Outreach Agent
==========================================
Automatically contacts high-quality leads (Score 9-10) with personalized emails.
Handles state management (status: contacted) and logs activity.
"""
import os
import sys
import logging
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv('.env.local')

from models import db, Lead, User, UserSMTPConfig, AutomationLog
from automation.mailer import send_smtp_email
from automation.qualifier import LeadQualifier

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("OutreachAgent")

class OutreachAgent:
    def __init__(self, app_context):
        self.app_context = app_context
        self.openai_key = os.getenv('OPENAI_API_KEY')
        self.qualifier = LeadQualifier(api_key=self.openai_key) if self.openai_key else None

    def generate_personalized_content(self, lead, user):
        """
        Uses AI to generate a highly personalized outreach email.
        """
        if not self.qualifier:
            return None, None

        prompt = f"""Write a personalized B2B outreach email for this lead:
Lead Name/Username: {lead.username}
Platform: {lead.platform}
Source (Subreddit/Tag): {lead.source}
Post Title: {lead.title}
Post Content: {lead.content[:1000]}
Problem Summary: {lead.problem_summary}

Context:
My Name: {user.name or "Founder of Ghost License Reaper"}
My Product: Ghost License Reaper (Detects unused SaaS licenses and saves 15-30% on bills).

Rules:
1. Don't sound like a bot. Be direct, helpful, and empathetic.
2. Mention something specific from their post.
3. Focus on the money they are losing (Loss Aversion).
4. Goal: Get them to click a link to run a free audit or reply.
5. Keep it under 150 words.

Return JSON:
{{
    "subject": "Clear, compelling subject line",
    "body": "The email body text"
}}"""

        try:
            # We reuse the qualifier's _call_openai method but with a custom prompt
            response_text = self.qualifier._call_openai([
                {"role": "system", "content": "You are an elite B2B Sales Representative specializing in high-conversion, low-pressure outreach. You response ONLY with JSON."},
                {"role": "user", "content": prompt}
            ])
            
            import json
            # Clean up response text if markdown or extra junk
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0].strip()
            
            content = json.loads(response_text)
            return content.get('subject'), content.get('body')
        except Exception as e:
            logger.error(f"Error generating content for lead {lead.id}: {e}")
            return None, None

    def generate_closing_content(self, lead, user):
        """
        Uses AI to detect intent and generate a closing email with a payment link.
        """
        if not self.qualifier:
            return None, None

        stripe_url = os.getenv('PRODUCT_PAYMENT_URL', 'https://buy.stripe.com/test_eVaeXkd8j7SgeYwdQQ')
        
        prompt = f"""The following lead has responded to our outreach. Analyze the response and write a follow-up to CLOSE THE SALE.
        
        Lead Response: {lead.last_reply_body}
        Context: They are interested in Ghost License Reaper.
        Goal: Get them to pay $299 for the setup and first month via this link: {stripe_url}
        
        Rules:
        1. If they have questions, answer them based on: 'Ghost License Reaper scans Gmail, finds unused licenses, saves 20%+, works in 5 mins'.
        2. Be extremely professional and confident.
        3. Include the payment link clearly.
        4. Keep it very short.
        
        Return JSON:
        {{
            "intent": "positive/neutral/negative",
            "subject": "Re: {lead.email_subject}",
            "body": "The closing email body"
        }}"""

        try:
            response_text = self.qualifier._call_openai([
                {"role": "system", "content": "You are a Senior Account Executive. Your goal is to close the deal. You response ONLY with JSON."},
                {"role": "user", "content": prompt}
            ])
            
            import json
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            
            content = json.loads(response_text)
            if content.get('intent') == 'positive':
                return content.get('subject'), content.get('body')
            return None, None
        except Exception as e:
            logger.error(f"Error generating closing for lead {lead.id}: {e}")
            return None, None

    def process_outreach_cycle(self, limit=5):
        """
        Runs both the initial outreach and the auto-closing phase.
        """
        sent_outreach = self._run_initial_outreach(limit)
        sent_closing = self._run_auto_closing(limit)
        return sent_outreach + sent_closing

    def _run_initial_outreach(self, limit):
        with self.app_context:
            leads = Lead.query.filter(
                Lead.status == 'new',
                Lead.score >= 9,
                Lead.email.isnot(None)
            ).limit(limit).all()

            emails_sent = 0
            for lead in leads:
                user = User.query.get(lead.user_id)
                if not user: continue
                smtp_config = UserSMTPConfig.query.filter_by(user_id=user.id).first()
                config_dict = None
                if smtp_config:
                    try:
                        config_dict = {
                            'server': smtp_config.smtp_server,
                            'port': smtp_config.smtp_port,
                            'username': smtp_config.smtp_username,
                            'password': smtp_config.get_password(),
                            'sender_name': smtp_config.sender_name
                        }
                    except: pass

                subject, body = self.generate_personalized_content(lead, user)
                if not subject or not body: continue

                success, _ = send_smtp_email(lead.email, subject, body, config=config_dict)
                if success:
                    lead.email_subject = subject
                    lead.status = 'contacted'
                    lead.email_sent_at = datetime.utcnow()
                    emails_sent += 1
            
            db.session.commit()
            return emails_sent

    def _run_auto_closing(self, limit):
        """
        Finds leads that responded positively and sends the payment link.
        """
        with self.app_context:
            # Note: 'responded' status is set by the Supabase Edge Function detect-outreach-replies
            leads = Lead.query.filter(
                Lead.status == 'responded',
                Lead.email.isnot(None)
            ).limit(limit).all()

            emails_sent = 0
            for lead in leads:
                user = User.query.get(lead.user_id)
                if not user: continue
                smtp_config = UserSMTPConfig.query.filter_by(user_id=user.id).first()
                config_dict = None
                if smtp_config:
                    try:
                        config_dict = {
                            'server': smtp_config.smtp_server, 'port': smtp_config.smtp_port,
                            'username': smtp_config.smtp_username, 'password': smtp_config.get_password(),
                            'sender_name': smtp_config.sender_name
                        }
                    except: pass

                subject, body = self.generate_closing_content(lead, user)
                if not subject or not body:
                    # If not positive or error, we might want to manually review
                    continue

                success, _ = send_smtp_email(lead.email, subject, body, config=config_dict)
                if success:
                    lead.status = 'closing' # Waiting for payment
                    lead.email_replied = True # Ensure this is marked
                    emails_sent += 1
                    logger.info(f"💰 Closing link sent to interested lead: {lead.email}")

            db.session.commit()
            return emails_sent

if __name__ == "__main__":
    from app import app
    agent = OutreachAgent(app.app_context())
    
    import argparse
    parser = argparse.ArgumentParser(description='Autonomous Outreach Agent')
    parser.add_argument('--test-lead', type=int, help='Lead ID to test outreach on')
    args = parser.parse_args()

    if args.test_lead:
        with app.app_context():
            lead = Lead.query.get(args.test_lead)
            if lead:
                user = User.query.get(lead.user_id)
                logger.info(f"Testing outreach for lead {lead.id}...")
                subject, body = agent.generate_personalized_content(lead, user)
                print(f"\nSUBJECT: {subject}\n")
                print(f"BODY:\n{body}\n")
            else:
                print("Lead not found.")
    else:
        logger.info("Starting production outreach cycle...")
        sent = agent.process_outreach_cycle()
        logger.info(f"Outreach cycle complete. Emails sent: {sent}")
