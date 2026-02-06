"""
Lead Finder AI - Social Profile Enrichment
==========================================
Enriches leads with social media profiles and company information.
$0 cost using public search and pattern matching.
"""
import os
import sys
import re
import logging
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass
import requests

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class SocialProfile:
    platform: str
    url: str
    username: Optional[str] = None
    confidence: float = 0.0


@dataclass
class CompanyInfo:
    name: Optional[str] = None
    domain: Optional[str] = None
    linkedin_url: Optional[str] = None
    industry: Optional[str] = None
    size_range: Optional[str] = None


@dataclass
class EnrichedLead:
    original_username: str
    original_platform: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    social_profiles: List[SocialProfile] = None
    company: Optional[CompanyInfo] = None
    enriched_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.social_profiles is None:
            self.social_profiles = []
    
    def to_dict(self):
        return {
            'original_username': self.original_username,
            'social_profiles': [{'platform': p.platform, 'url': p.url} for p in self.social_profiles],
            'company': {'name': self.company.name if self.company else None},
        }


class SocialEnricher:
    LINKEDIN_PATTERNS = [r'linkedin\.com/in/([a-zA-Z0-9_-]+)']
    TWITTER_PATTERNS = [r'twitter\.com/([a-zA-Z0-9_]+)', r'x\.com/([a-zA-Z0-9_]+)']
    GITHUB_PATTERNS = [r'github\.com/([a-zA-Z0-9_-]+)']
    
    FREE_EMAIL_DOMAINS = {'gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com', 'icloud.com'}
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': 'Mozilla/5.0'})
    
    def find_linkedin_from_reddit(self, username: str) -> Optional[SocialProfile]:
        try:
            resp = self.session.get(f"https://www.reddit.com/user/{username}/about.json", timeout=10)
            if resp.status_code != 200:
                return None
            desc = resp.json().get('data', {}).get('subreddit', {}).get('public_description', '')
            for pattern in self.LINKEDIN_PATTERNS:
                match = re.search(pattern, desc)
                if match:
                    return SocialProfile('linkedin', f"https://linkedin.com/in/{match.group(1)}", match.group(1), 0.8)
        except Exception:
            pass
        return None
    
    def find_github_from_hackernews(self, username: str) -> Optional[SocialProfile]:
        try:
            resp = self.session.get(f"https://hacker-news.firebaseio.com/v0/user/{username}.json", timeout=10)
            if resp.status_code != 200:
                return None
            about = resp.json().get('about', '')
            for pattern in self.GITHUB_PATTERNS:
                match = re.search(pattern, about)
                if match:
                    return SocialProfile('github', f"https://github.com/{match.group(1)}", match.group(1), 0.9)
        except Exception:
            pass
        return None
    
    def detect_company_from_email(self, email: str) -> Optional[CompanyInfo]:
        if not email:
            return None
        try:
            domain = email.split('@')[1].lower()
            if domain in self.FREE_EMAIL_DOMAINS:
                return None
            return CompanyInfo(domain.split('.')[0].title(), domain, f"https://linkedin.com/company/{domain.split('.')[0]}")
        except Exception:
            return None
    
    def enrich_lead(self, username: str, platform: str, email: str = None, content: str = None) -> EnrichedLead:
        enriched = EnrichedLead(username, platform, email, enriched_at=datetime.utcnow())
        
        if platform == 'reddit':
            linkedin = self.find_linkedin_from_reddit(username)
            if linkedin:
                enriched.social_profiles.append(linkedin)
        elif platform == 'hackernews':
            github = self.find_github_from_hackernews(username)
            if github:
                enriched.social_profiles.append(github)
        
        if email:
            enriched.company = self.detect_company_from_email(email)
        
        return enriched


def get_enricher() -> SocialEnricher:
    return SocialEnricher()
