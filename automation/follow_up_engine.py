"""
Lead Finder AI - Auto Follow-Up Sequence Engine
================================================
Manages automated email follow-up sequences for leads.

Key Features:
- Configurable follow-up sequences (3-7 emails)
- Smart timing with customizable delays
- Personalization using AI-generated content
- Stop on reply detection
- A/B testing support for subject lines

Research shows 80% of sales require 5+ follow-ups.
This engine automates the tedious follow-up process.
"""
import os
import sys
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FollowUpStatus(Enum):
    PENDING = "pending"
    SENT = "sent"
    SKIPPED = "skipped"  # User replied before this was sent
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class FollowUpEmail:
    """Represents a single follow-up email in a sequence"""
    sequence_position: int  # 1, 2, 3, etc.
    delay_days: int  # Days after previous email
    subject_template: str
    body_template: str
    status: FollowUpStatus = FollowUpStatus.PENDING
    scheduled_for: Optional[datetime] = None
    sent_at: Optional[datetime] = None
    
    def to_dict(self):
        return {
            'position': self.sequence_position,
            'delay_days': self.delay_days,
            'subject': self.subject_template,
            'status': self.status.value,
            'scheduled_for': self.scheduled_for.isoformat() if self.scheduled_for else None,
            'sent_at': self.sent_at.isoformat() if self.sent_at else None,
        }


@dataclass
class FollowUpSequence:
    """A complete follow-up sequence configuration"""
    name: str
    description: str
    emails: List[FollowUpEmail] = field(default_factory=list)
    is_active: bool = True
    
    def to_dict(self):
        return {
            'name': self.name,
            'description': self.description,
            'emails': [e.to_dict() for e in self.emails],
            'total_emails': len(self.emails),
            'is_active': self.is_active,
        }


# Pre-built sequences for different use cases
DEFAULT_SEQUENCES = {
    "saas_demo": FollowUpSequence(
        name="SaaS Demo Request",
        description="For leads interested in software demos",
        emails=[
            FollowUpEmail(
                sequence_position=1,
                delay_days=0,
                subject_template="Re: Your {platform} post about {topic}",
                body_template="""Hi {name},

I saw your post on {platform} about {problem_summary}.

I've helped several {industry} companies solve exactly this. Would love to show you how we approach it.

Do you have 15 minutes this week for a quick call?

Best,
{sender_name}"""
            ),
            FollowUpEmail(
                sequence_position=2,
                delay_days=2,
                subject_template="Quick follow-up - {topic}",
                body_template="""Hi {name},

Just wanted to follow up on my previous message.

I know how frustrating {problem_summary} can be - I've been there.

Here's a quick case study of how we helped a similar company: [Link]

Worth a quick chat?

{sender_name}"""
            ),
            FollowUpEmail(
                sequence_position=3,
                delay_days=4,
                subject_template="One more thing about {topic}",
                body_template="""Hi {name},

I wanted to share one more thought about your {platform} post.

Many {industry} leaders are using automation to solve {problem_summary}.

Here's what I'd suggest:
1. [Specific tip 1]
2. [Specific tip 2]

Happy to explain more - no pressure.

{sender_name}"""
            ),
            FollowUpEmail(
                sequence_position=4,
                delay_days=7,
                subject_template="Last try - {topic}",
                body_template="""Hi {name},

I'll keep this short - I've reached out a few times about {problem_summary}.

If you're not interested, no worries at all. Just let me know and I'll stop following up.

But if timing was just off, I'm here when you're ready.

{sender_name}"""
            ),
        ]
    ),
    
    "local_business": FollowUpSequence(
        name="Local Business Outreach",
        description="For local business lead generation",
        emails=[
            FollowUpEmail(
                sequence_position=1,
                delay_days=0,
                subject_template="Helping {business_name} get more customers",
                body_template="""Hi {name},

I noticed {business_name} doesn't have [specific thing they're missing].

This is costing you customers - here's why:
- [Stat 1]
- [Stat 2]

I help local businesses fix this. Can I show you how?

{sender_name}"""
            ),
            FollowUpEmail(
                sequence_position=2,
                delay_days=3,
                subject_template="Free audit for {business_name}",
                body_template="""Hi {name},

I did a quick (free) analysis of {business_name}'s online presence.

Here's what I found:
✓ [Positive thing]
✗ [Thing to improve]
✗ [Another thing to improve]

Want the full report? Takes 2 minutes to review together.

{sender_name}"""
            ),
            FollowUpEmail(
                sequence_position=3,
                delay_days=5,
                subject_template="Your competitors are doing this...",
                body_template="""Hi {name},

I wanted to share something interesting.

I looked at 3 of your competitors in {location}. They're all doing [specific thing].

Not saying you need to copy them, but it might be worth discussing.

Quick call this week?

{sender_name}"""
            ),
        ]
    ),
    
    "freelance_services": FollowUpSequence(
        name="Freelance Services",
        description="For selling freelance/consulting services",
        emails=[
            FollowUpEmail(
                sequence_position=1,
                delay_days=0,
                subject_template="Saw your post about {topic}",
                body_template="""Hi {name},

Your {platform} post about {problem_summary} caught my attention.

I'm a {profession} who specializes in exactly this.

Would you be open to a quick chat about how I could help?

{sender_name}"""
            ),
            FollowUpEmail(
                sequence_position=2,
                delay_days=2,
                subject_template="Ideas for {topic}",
                body_template="""Hi {name},

Following up on my message about {problem_summary}.

Here are 3 quick wins you could implement today:
1. {tip_1}
2. {tip_2}
3. {tip_3}

If you want, I can help with the heavy lifting.

{sender_name}"""
            ),
            FollowUpEmail(
                sequence_position=3,
                delay_days=5,
                subject_template="Still thinking about {topic}?",
                body_template="""Hi {name},

I know you're busy, so I'll be brief.

If {problem_summary} is still on your mind, I'm here to help.

No hard sell - just a conversation to see if I can add value.

{sender_name}"""
            ),
        ]
    ),
}


class FollowUpEngine:
    """
    Manages follow-up sequences for leads.
    Handles scheduling, sending, and tracking of automated emails.
    """
    
    def __init__(self):
        self.sequences = DEFAULT_SEQUENCES.copy()
    
    def get_sequence(self, name: str) -> Optional[FollowUpSequence]:
        """Get a sequence by name"""
        return self.sequences.get(name)
    
    def list_sequences(self) -> List[Dict]:
        """List all available sequences"""
        return [seq.to_dict() for seq in self.sequences.values()]
    
    def create_follow_up_schedule(
        self,
        lead_id: int,
        sequence_name: str,
        start_date: datetime = None
    ) -> List[Dict]:
        """
        Create a follow-up schedule for a lead.
        Returns list of scheduled emails with dates.
        """
        sequence = self.get_sequence(sequence_name)
        if not sequence:
            raise ValueError(f"Unknown sequence: {sequence_name}")
        
        start = start_date or datetime.utcnow()
        schedule = []
        current_date = start
        
        for email in sequence.emails:
            scheduled_time = current_date + timedelta(days=email.delay_days)
            
            schedule.append({
                'lead_id': lead_id,
                'sequence_name': sequence_name,
                'position': email.sequence_position,
                'scheduled_for': scheduled_time,
                'subject_template': email.subject_template,
                'body_template': email.body_template,
                'status': FollowUpStatus.PENDING.value,
            })
            
            current_date = scheduled_time
        
        return schedule
    
    def personalize_email(
        self,
        template: str,
        lead_data: Dict,
        sender_data: Dict
    ) -> str:
        """
        Replace template variables with actual data.
        
        Available variables:
        - {name}: Lead's name/username
        - {platform}: Where we found them
        - {topic}: What they posted about
        - {problem_summary}: AI-generated summary
        - {industry}: Detected industry
        - {sender_name}: Your name
        - {business_name}: Their business name
        - {location}: Their location
        """
        replacements = {
            'name': lead_data.get('name') or lead_data.get('username', 'there'),
            'platform': lead_data.get('platform', 'the internet'),
            'topic': (lead_data.get('title', '')[:50] + '...') if lead_data.get('title') else 'your recent post',
            'problem_summary': lead_data.get('problem_summary', 'the challenge you mentioned'),
            'industry': lead_data.get('industry', 'your industry'),
            'business_name': lead_data.get('business_name', 'your business'),
            'location': lead_data.get('location', 'your area'),
            'sender_name': sender_data.get('name', 'Your Name'),
            'profession': sender_data.get('profession', 'professional'),
            'tip_1': 'Automate your outreach',
            'tip_2': 'Use data-driven targeting',
            'tip_3': 'Follow up consistently',
        }
        
        result = template
        for key, value in replacements.items():
            result = result.replace('{' + key + '}', str(value))
        
        return result
    
    def get_next_pending_emails(self, limit: int = 50) -> List[Dict]:
        """
        Get next emails that should be sent.
        Query the database for pending follow-ups where scheduled_for <= now.
        """
        try:
            # We need to use raw SQL or SQLAlchemy here. 
            # Since this class might be used outside app context, we import inside.
            from models import db
            from sqlalchemy import text
            
            # Using raw SQL for performance and clarity on the specific fields
            sql = text("""
                SELECT id, lead_id, sequence_name, position, subject, body, scheduled_for
                FROM lead_follow_ups
                WHERE status = 'pending' 
                AND scheduled_for <= :now
                ORDER BY scheduled_for ASC
                LIMIT :limit
            """)
            
            result = db.session.execute(sql, {
                'now': datetime.utcnow(),
                'limit': limit
            }).fetchall()
            
            pending_emails = []
            for row in result:
                pending_emails.append({
                    'id': row.id,
                    'lead_id': row.lead_id,
                    'sequence_name': row.sequence_name,
                    'position': row.position,
                    'subject': row.subject,
                    'body': row.body,
                    'scheduled_for': row.scheduled_for
                })
                
            return pending_emails
            
        except ImportError:
            logger.error("Could not import database models. Ensure app context is active.")
            return []
        except Exception as e:
            logger.error(f"Error fetching pending emails: {e}")
            return []
    
    def should_continue_sequence(self, lead_id: int) -> Tuple[bool, str]:
        """
        Check if we should continue the sequence for a lead.
        Returns (should_continue, reason)
        
        Stop conditions:
        - Lead has replied
        - Lead has been marked as converted
        - Lead has unsubscribed (not yet implemented fields but safe defaults)
        - Lead status is not 'new' or 'contacted'
        """
        try:
            from models import Lead
            lead = Lead.query.get(lead_id)
            
            if not lead:
                return False, "Lead not found"
            
            # 1. Check if lead replied
            if lead.email_replied:
                return False, "Lead replied"
            
            # 2. Check status
            STOP_STATUSES = ['replied', 'converted', 'archived', 'bad_fit']
            if lead.status in STOP_STATUSES:
                return False, f"Lead status is {lead.status}"
            
            return True, "Continue"
            
        except Exception as e:
            logger.error(f"Error checking sequence continuation for lead {lead_id}: {e}")
            # Fail safe: iterate but log error
            return True, "Error checking status (fail-open)"


# Database model for follow-up tracking
FOLLOWUP_MODEL_SQL = """
-- Follow-up sequence tracking table
CREATE TABLE IF NOT EXISTS lead_follow_ups (
    id SERIAL PRIMARY KEY,
    lead_id INTEGER NOT NULL REFERENCES leads(id) ON DELETE CASCADE,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    sequence_name VARCHAR(100) NOT NULL,
    position INTEGER NOT NULL,
    scheduled_for TIMESTAMP NOT NULL,
    sent_at TIMESTAMP,
    status VARCHAR(20) DEFAULT 'pending',
    subject TEXT,
    body TEXT,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    UNIQUE(lead_id, sequence_name, position)
);

CREATE INDEX IF NOT EXISTS idx_followups_scheduled 
ON lead_follow_ups(scheduled_for) 
WHERE status = 'pending';

CREATE INDEX IF NOT EXISTS idx_followups_lead 
ON lead_follow_ups(lead_id);
"""


def get_engine() -> FollowUpEngine:
    """Get follow-up engine singleton"""
    return FollowUpEngine()


if __name__ == "__main__":
    # Demo
    engine = FollowUpEngine()
    
    print("\n" + "=" * 60)
    print("FOLLOW-UP SEQUENCES AVAILABLE")
    print("=" * 60)
    
    for seq in engine.list_sequences():
        print(f"\n📧 {seq['name']}")
        print(f"   {seq['description']}")
        print(f"   Total emails: {seq['total_emails']}")
    
    # Example schedule
    print("\n" + "=" * 60)
    print("EXAMPLE SCHEDULE (SaaS Demo)")
    print("=" * 60)
    
    schedule = engine.create_follow_up_schedule(
        lead_id=1,
        sequence_name="saas_demo",
        start_date=datetime.utcnow()
    )
    
    for email in schedule:
        print(f"\n📅 Email #{email['position']}")
        print(f"   Scheduled: {email['scheduled_for']}")
        print(f"   Subject: {email['subject_template'][:50]}...")
