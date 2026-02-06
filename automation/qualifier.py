"""
Lead Finder AI - AI Lead Qualifier
Uses OpenAI to score and qualify leads based on urgency, budget, and fit
"""
import os
import json
import logging
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict

from openai import OpenAI, APIError, RateLimitError, APIConnectionError
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class QualifiedLead:
    """Qualified lead with AI scoring"""
    # Original data
    username: str
    platform: str
    title: str
    content: str
    post_url: str
    profile_url: Optional[str]
    email: Optional[str]
    
    # AI-generated scores
    score: int  # 1-10 overall fit
    urgency: int  # 1-10 how urgent is their need
    budget_indicator: str  # low, medium, high, enterprise
    market_size: str  # small, medium, large
    willingness_to_pay: int  # 1-10
    
    # AI-generated insights
    problem_summary: str
    pain_points: List[str]
    recommended_approach: str


class LeadQualifier:
    """Uses AI to qualify and score leads"""
    
    SYSTEM_PROMPT = """You are an expert B2B sales qualification AI. Your job is to analyze leads 
found on social media and forums, and score them based on:

1. **Urgency (1-10)**: How urgently do they need a solution?
   - 9-10: Desperate, need solution NOW
   - 7-8: Active pain, searching for solutions
   - 5-6: Interested, exploring options
   - 3-4: Mild curiosity
   - 1-2: Just browsing

2. **Score (1-10)**: Overall qualification as a potential customer
   - Consider: pain level, specificity, engagement, decision-maker signals

3. **Budget Indicator**: Estimate their likely budget
   - low: <$50/month
   - medium: $50-200/month  
   - high: $200-500/month
   - enterprise: $500+/month

4. **Market Size**:
   - small: Individual/freelancer
   - medium: Small team/startup
   - large: Established company

5. **Willingness to Pay (1-10)**: How likely are they to pay for a solution?

6. **Problem Summary**: One sentence describing their core problem.

7. **Pain Points**: 2-4 specific pain points mentioned or implied.

8. **Recommended Approach**: How should a salesperson approach this lead?

Be realistic and conservative with scoring. Most leads are NOT high quality.
Look for buying signals: urgency language, specific problems, budget mentions, 
frustration with current solutions, requests for recommendations.

Respond ONLY with valid JSON, no markdown formatting."""

    def __init__(self, api_key: str, model: str = "gpt-4o-mini"):
        self.client = OpenAI(api_key=api_key)
        self.model = model
    
    @retry(
        retry=retry_if_exception_type((RateLimitError, APIConnectionError, APIError)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=30),
        before_sleep=before_sleep_log(logger, logging.WARNING)
    )
    def _call_openai(self, messages: List[Dict]) -> str:
        """Call OpenAI API with retry logic for resilience"""
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.3,
            max_tokens=500
        )
        return response.choices[0].message.content.strip()
    
    def qualify_lead(self, lead_data: Dict) -> Optional[QualifiedLead]:
        """Qualify a single lead using AI"""
        
        prompt = f"""Analyze this lead and provide qualification scores:

Platform: {lead_data['platform']}
Username: {lead_data['username']}
Title: {lead_data['title']}
Content: {lead_data['content'][:1500]}
Post URL: {lead_data['post_url']}

Respond with JSON in this exact format:
{{
    "score": <1-10>,
    "urgency": <1-10>,
    "budget_indicator": "<low|medium|high|enterprise>",
    "market_size": "<small|medium|large>",
    "willingness_to_pay": <1-10>,
    "problem_summary": "<one sentence summary>",
    "pain_points": ["<point 1>", "<point 2>"],
    "recommended_approach": "<how to approach this lead>"
}}"""

        try:
            result_text = self._call_openai([
                {"role": "system", "content": self.SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ])
            
            # Clean up any markdown formatting
            if result_text.startswith('```'):
                result_text = result_text.split('```')[1]
                if result_text.startswith('json'):
                    result_text = result_text[4:]
                result_text = result_text.strip()
            
            result = json.loads(result_text)
            
            return QualifiedLead(
                username=lead_data['username'],
                platform=lead_data['platform'],
                title=lead_data['title'],
                content=lead_data['content'],
                post_url=lead_data['post_url'],
                profile_url=lead_data.get('profile_url'),
                email=lead_data.get('email'),
                score=min(10, max(1, result.get('score', 5))),
                urgency=min(10, max(1, result.get('urgency', 5))),
                budget_indicator=result.get('budget_indicator', 'medium'),
                market_size=result.get('market_size', 'small'),
                willingness_to_pay=min(10, max(1, result.get('willingness_to_pay', 5))),
                problem_summary=result.get('problem_summary', ''),
                pain_points=result.get('pain_points', []),
                recommended_approach=result.get('recommended_approach', '')
            )
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI response: {e}")
            return None
        except Exception as e:
            logger.error(f"Error qualifying lead: {e}")
            return None
    
    def qualify_batch(
        self, 
        leads: List[Dict], 
        min_score: int = 5,
        max_to_process: int = 100
    ) -> List[QualifiedLead]:
        """Qualify a batch of leads and filter by minimum score"""
        
        qualified = []
        
        for i, lead_data in enumerate(leads[:max_to_process]):
            logger.info(f"Qualifying lead {i+1}/{min(len(leads), max_to_process)}")
            
            qualified_lead = self.qualify_lead(lead_data)
            
            if qualified_lead and qualified_lead.score >= min_score:
                qualified.append(qualified_lead)
                logger.info(f"  -> Score: {qualified_lead.score}/10 ✓")
            elif qualified_lead:
                logger.info(f"  -> Score: {qualified_lead.score}/10 (below threshold)")
            else:
                logger.info(f"  -> Failed to qualify")
        
        # Sort by score descending
        qualified.sort(key=lambda x: (x.score, x.urgency), reverse=True)
        
        logger.info(f"Qualified {len(qualified)} leads out of {min(len(leads), max_to_process)}")
        return qualified
    
    def generate_lead_report(self, leads: List[QualifiedLead]) -> str:
        """Generate a summary report of qualified leads"""
        
        if not leads:
            return "No qualified leads found."
        
        report = []
        report.append(f"# Lead Qualification Report")
        report.append(f"Total Qualified Leads: {len(leads)}")
        report.append("")
        
        # Score distribution
        high_score = len([l for l in leads if l.score >= 8])
        medium_score = len([l for l in leads if 5 <= l.score < 8])
        low_score = len([l for l in leads if l.score < 5])
        
        report.append("## Score Distribution")
        report.append(f"- High (8-10): {high_score}")
        report.append(f"- Medium (5-7): {medium_score}")
        report.append(f"- Low (1-4): {low_score}")
        report.append("")
        
        # Platform breakdown
        platforms = {}
        for lead in leads:
            platforms[lead.platform] = platforms.get(lead.platform, 0) + 1
        
        report.append("## By Platform")
        for platform, count in platforms.items():
            report.append(f"- {platform}: {count}")
        report.append("")
        
        # Top leads
        report.append("## Top 10 Leads")
        for i, lead in enumerate(leads[:10], 1):
            report.append(f"\n### {i}. @{lead.username} ({lead.platform})")
            report.append(f"**Score:** {lead.score}/10 | **Urgency:** {lead.urgency}/10")
            report.append(f"**Budget:** {lead.budget_indicator} | **Market:** {lead.market_size}")
            report.append(f"**Problem:** {lead.problem_summary}")
            report.append(f"**URL:** {lead.post_url}")
        
        return "\n".join(report)


# Standalone test
if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    
    qualifier = LeadQualifier(api_key=os.getenv('OPENAI_API_KEY'))
    
    # Test lead
    test_lead = {
        'username': 'startup_founder',
        'platform': 'reddit',
        'title': 'Looking for a tool to automate my lead generation - spending 4 hours/day on this!',
        'content': """I'm running a small marketing agency and I'm drowning in manual lead generation work. 
        I spend at least 4 hours every day scraping LinkedIn, Twitter, and Reddit for potential clients.
        My current process is: search for keywords -> copy to spreadsheet -> research each person -> write cold email.
        This is killing my productivity. I've looked at tools like Apollo and ZoomInfo but they're too expensive ($500+/month).
        Would pay up to $150/month for something that could automate even half of this. Anyone have recommendations?""",
        'post_url': 'https://reddit.com/r/Entrepreneur/example',
        'profile_url': 'https://reddit.com/user/startup_founder'
    }
    
    result = qualifier.qualify_lead(test_lead)
    
    if result:
        print(f"\n{'='*50}")
        print(f"Lead: @{result.username}")
        print(f"Score: {result.score}/10")
        print(f"Urgency: {result.urgency}/10")
        print(f"Budget: {result.budget_indicator}")
        print(f"Market Size: {result.market_size}")
        print(f"Willingness to Pay: {result.willingness_to_pay}/10")
        print(f"\nProblem: {result.problem_summary}")
        print(f"\nPain Points:")
        for point in result.pain_points:
            print(f"  - {point}")
        print(f"\nRecommended Approach: {result.recommended_approach}")
