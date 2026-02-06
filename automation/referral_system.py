"""
Lead Finder AI - Viral Referral System
=======================================
Referral system for Product-Led Growth (PLG).
"Invite friends, earn free leads"
"""
import os
import sys
import uuid
import hashlib
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple
from dataclasses import dataclass

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Referral Rewards Configuration
REFERRAL_REWARDS = {
    'referrer': {
        'free_leads': 50,          # Leads for inviter
        'free_emails': 25,         # Extra emails
        'trial_days': 7,           # Pro trial days
    },
    'referee': {
        'free_leads': 25,          # Leads for invitee
        'trial_days': 14,          # Extended trial
        'discount_percent': 20,    # First month discount
    },
    'tiers': {
        'bronze': {'referrals': 3, 'reward': '1 month free'},
        'silver': {'referrals': 10, 'reward': '3 months free'},
        'gold': {'referrals': 25, 'reward': 'Lifetime Pro'},
    }
}


@dataclass
class ReferralCode:
    code: str
    user_id: int
    created_at: datetime
    uses: int = 0
    max_uses: int = 100
    expires_at: Optional[datetime] = None
    
    def is_valid(self) -> bool:
        if self.max_uses and self.uses >= self.max_uses:
            return False
        if self.expires_at and datetime.utcnow() > self.expires_at:
            return False
        return True


@dataclass
class Referral:
    referrer_id: int
    referee_id: int
    code_used: str
    status: str  # pending, completed, rewarded
    created_at: datetime
    completed_at: Optional[datetime] = None


class ReferralEngine:
    """Manages referral codes and rewards"""
    
    def generate_referral_code(self, user_id: int, user_email: str) -> str:
        """Generate unique referral code for a user"""
        secret = os.getenv('SECRET_KEY', 'default')
        base = f"{user_id}:{user_email}:{secret}"
        code_hash = hashlib.sha256(base.encode()).hexdigest()[:8].upper()
        return f"LF-{code_hash}"
    
    def generate_referral_link(self, code: str, base_url: str = None) -> str:
        """Generate shareable referral link"""
        url = base_url or os.getenv('APP_URL', 'http://localhost:5000')
        return f"{url}/signup?ref={code}"
    
    def validate_code(self, code: str) -> Tuple[bool, str]:
        """Validate referral code"""
        if not code or len(code) < 5:
            return False, "Invalid code format"
        if not code.startswith('LF-'):
            return False, "Invalid code format"
        return True, "Valid"
    
    def calculate_rewards(self, referrer_referrals: int) -> Dict:
        """Calculate rewards based on referral count"""
        rewards = {'tier': 'none', 'next_tier': 'bronze', 'referrals_needed': 3}
        
        for tier, config in REFERRAL_REWARDS['tiers'].items():
            if referrer_referrals >= config['referrals']:
                rewards['tier'] = tier
                rewards['reward'] = config['reward']
        
        # Calculate next tier
        if rewards['tier'] == 'none':
            rewards['next_tier'] = 'bronze'
            rewards['referrals_needed'] = 3 - referrer_referrals
        elif rewards['tier'] == 'bronze':
            rewards['next_tier'] = 'silver'
            rewards['referrals_needed'] = 10 - referrer_referrals
        elif rewards['tier'] == 'silver':
            rewards['next_tier'] = 'gold'
            rewards['referrals_needed'] = 25 - referrer_referrals
        else:
            rewards['next_tier'] = None
            rewards['referrals_needed'] = 0
        
        return rewards
    
    def get_share_messages(self, referral_link: str) -> Dict:
        """Pre-written share messages for different platforms"""
        return {
            'twitter': f"I've been finding amazing B2B leads with @LeadFinderAI 🚀 Use my link for free leads: {referral_link}",
            'linkedin': f"Game-changer for lead generation! Lead Finder AI helped me find 50+ qualified leads this week. Try it free: {referral_link}",
            'email_subject': "Try this tool I've been using for lead gen",
            'email_body': f"Hey,\n\nI found this tool called Lead Finder AI that's been amazing for finding B2B leads.\n\nUse my referral link and we both get free leads: {referral_link}\n\nLet me know what you think!",
            'whatsapp': f"Check out Lead Finder AI for B2B leads! Use my link: {referral_link}",
        }


# SQL for referral tables
REFERRAL_TABLES_SQL = """
CREATE TABLE IF NOT EXISTS referral_codes (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    code VARCHAR(20) UNIQUE NOT NULL,
    uses INTEGER DEFAULT 0,
    max_uses INTEGER DEFAULT 100,
    expires_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS referrals (
    id SERIAL PRIMARY KEY,
    referrer_id INTEGER NOT NULL REFERENCES users(id),
    referee_id INTEGER NOT NULL REFERENCES users(id),
    code_used VARCHAR(20) NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    reward_given BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP,
    UNIQUE(referee_id)
);

-- Add referral columns to users
ALTER TABLE users ADD COLUMN IF NOT EXISTS referral_code VARCHAR(20);
ALTER TABLE users ADD COLUMN IF NOT EXISTS referred_by INTEGER REFERENCES users(id);
ALTER TABLE users ADD COLUMN IF NOT EXISTS total_referrals INTEGER DEFAULT 0;
ALTER TABLE users ADD COLUMN IF NOT EXISTS referral_tier VARCHAR(20) DEFAULT 'none';

CREATE INDEX IF NOT EXISTS idx_referral_codes ON referral_codes(code);
"""


def get_engine() -> ReferralEngine:
    return ReferralEngine()


if __name__ == "__main__":
    engine = ReferralEngine()
    print("\n" + "=" * 50)
    print("REFERRAL SYSTEM DEMO")
    print("=" * 50)
    
    code = engine.generate_referral_code(1, "user@example.com")
    link = engine.generate_referral_link(code, "https://leadfinderai.com")
    
    print(f"\n🎁 Referral Code: {code}")
    print(f"🔗 Referral Link: {link}")
    print(f"\n📱 Share Messages:")
    for platform, msg in engine.get_share_messages(link).items():
        print(f"   {platform}: {msg[:80]}...")
