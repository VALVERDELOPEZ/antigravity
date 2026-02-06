"""
Lead Finder AI - AI-Powered Lead Generator
Generates realistic leads using OpenAI when real APIs are not configured
"""
import json
import random
from datetime import datetime, timedelta
from openai import OpenAI
import os

def generate_leads_with_ai(keywords: list, num_leads: int = 5, user_id: int = None):
    """
    Generate realistic leads using OpenAI based on user keywords
    This is used when Reddit/Twitter APIs are not configured
    """
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("Error: OPENAI_API_KEY not configured")
        return []
    
    client = OpenAI(api_key=api_key)
    
    platforms = ['reddit', 'twitter', 'hackernews', 'indiehackers', 'linkedin']
    
    prompt = f"""Generate {num_leads} realistic social media posts from people who might be potential leads for a B2B service.

These people should be expressing problems, frustrations, or needs related to these topics: {', '.join(keywords)}

For each lead, provide:
- platform: one of {platforms}
- username: a realistic but fictional username
- title: the post title or tweet first line
- content: the full post content (2-4 sentences, realistic tone)
- urgency: 1-10 (how urgent is their need)
- budget_indicator: "low", "medium", "high", or "enterprise"
- pain_points: list of 2-3 specific pain points

Return as a JSON array. Make the posts sound authentic, with typos, casual language, and real frustrations that B2B buyers express.

Example format:
[
  {{
    "platform": "reddit",
    "username": "startup_founder_23",
    "title": "Spending 4 hours daily on lead gen - there has to be a better way",
    "content": "Running a SaaS and I'm literally spending half my day sending cold emails that get ignored. Is there any tool that actually works? Budget around $100-200/mo.",
    "urgency": 8,
    "budget_indicator": "medium",
    "pain_points": ["manual work", "low response rates", "time consuming"]
  }}
]"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a data generator that creates realistic social media posts. Always respond with valid JSON only, no markdown."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.9,
            max_tokens=2000
        )
        
        content = response.choices[0].message.content.strip()
        # Clean up any markdown formatting
        if content.startswith('```'):
            content = content.split('```')[1]
            if content.startswith('json'):
                content = content[4:]
        
        leads_data = json.loads(content)
        
        # Add metadata
        for lead in leads_data:
            lead['source_created_at'] = (datetime.utcnow() - timedelta(hours=random.randint(1, 48))).isoformat()
            lead['post_url'] = f"https://{lead['platform']}.com/post/{random.randint(10000, 99999)}"
            lead['generated_by'] = 'openai'
        
        print(f"✓ Generated {len(leads_data)} leads with OpenAI")
        return leads_data
        
    except json.JSONDecodeError as e:
        print(f"Error parsing OpenAI response: {e}")
        print(f"Raw response: {content[:500]}")
        return []
    except Exception as e:
        print(f"Error generating leads: {e}")
        return []


def score_lead_with_ai(lead_data: dict) -> dict:
    """
    Score a lead using OpenAI to determine its quality.
    Detects language and responds in the same language.
    """
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        return {'score': 5, 'reason': 'API not configured'}
    
    client = OpenAI(api_key=api_key)
    
    # Get language from lead or detect it
    lead_language = lead_data.get('language', 'en')
    
    # Language-specific instructions
    language_instructions = {
        'en': "Respond in English.",
        'es': "Responde en español.",
        'pt': "Responda em português.",
        'fr': "Répondez en français."
    }
    
    lang_instruction = language_instructions.get(lead_language, "Respond in English.")
    
    prompt = f"""Analyze this social media post and score the person as a potential B2B lead.
{lang_instruction}

The post appears to be in {lead_language.upper()}.

Platform: {lead_data.get('platform', 'unknown')}
Post Title: {lead_data.get('title', '')}
Content: {lead_data.get('content', '')}
Username: {lead_data.get('username', '')}

Score this lead from 1-10 based on:
- Urgency of their need (are they ready to buy now?)
- Budget indicators (do they seem to have money to spend?)
- Problem clarity (is their pain point clear?)
- Decision maker likelihood (do they seem like they can make buying decisions?)

Return JSON only (with responses in {lead_language.upper()} where applicable):
{{
  "score": <1-10>,
  "urgency": <1-10>,
  "budget_indicator": "low|medium|high|enterprise",
  "problem_summary": "<one sentence summary of their main problem - in {lead_language.upper()}>",
  "recommended_approach": "<how to approach them - in {lead_language.upper()}>",
  "pain_points": ["<pain1>", "<pain2>"],
  "language_detected": "{lead_language}",
  "reason": "<why this score - in {lead_language.upper()}>"
}}"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": f"You are a multilingual lead qualification expert. {lang_instruction} Always respond with valid JSON only."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=500
        )
        
        content = response.choices[0].message.content.strip()
        if content.startswith('```'):
            content = content.split('```')[1]
            if content.startswith('json'):
                content = content[4:]
        
        result = json.loads(content)
        result['language'] = lead_language  # Ensure language is tracked
        return result
        
    except Exception as e:
        print(f"Error scoring lead: {e}")
        return {'score': 5, 'reason': str(e), 'language': lead_language}


def generate_email_with_ai(lead_data: dict, sender_info: dict = None) -> dict:
    """
    Generate a personalized cold email for a lead using OpenAI.
    Respects the lead's language - writes email in the same language as the post.
    """
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        return {'subject': '', 'body': '', 'error': 'API not configured'}
    
    client = OpenAI(api_key=api_key)
    
    sender_name = sender_info.get('name', 'Alex') if sender_info else 'Alex'
    sender_company = sender_info.get('company', 'Lead Finder AI') if sender_info else 'Lead Finder AI'
    
    # Get lead's language
    lead_language = lead_data.get('language', 'en')
    
    # Language-specific instructions
    language_config = {
        'en': {
            'instruction': "Write the email in ENGLISH.",
            'system': "You are an expert at writing personalized cold emails that get responses. Write in English.",
        },
        'es': {
            'instruction': "Escribe el email EN ESPAÑOL. El lead habla español.",
            'system': "Eres un experto escribiendo emails fríos personalizados que consiguen respuestas. Escribe en español.",
        },
        'pt': {
            'instruction': "Escreva o email EM PORTUGUÊS. O lead fala português.",
            'system': "Você é um especialista em escrever emails frios personalizados que recebem respostas. Escreva em português.",
        },
        'fr': {
            'instruction': "Écrivez l'email EN FRANÇAIS. Le lead parle français.",
            'system': "Vous êtes un expert en rédaction d'emails à froid personnalisés qui obtiennent des réponses. Écrivez en français.",
        }
    }
    
    lang_config = language_config.get(lead_language, language_config['en'])
    
    prompt = f"""Write a personalized cold email to this potential lead.
{lang_config['instruction']}

The lead's post (in {lead_language.upper()}):
Platform: {lead_data.get('platform', '')}
Title: {lead_data.get('title', '')}
Content: {lead_data.get('content', '')}
Their pain points: {lead_data.get('pain_points', [])}

Write an email that:
1. References their specific problem (don't be generic)
2. Shows empathy for their situation
3. Briefly mentions how you can help
4. Has a soft call-to-action (not pushy)
5. Feels human, not like a template
6. Is short (under 150 words)
7. IS WRITTEN IN {lead_language.upper()} - VERY IMPORTANT!

Sender: {sender_name} from {sender_company}

Return JSON (with subject and body in {lead_language.upper()}):
{{
  "subject": "<catchy but professional subject line in {lead_language.upper()}>",
  "body": "<the email body in {lead_language.upper()}>",
  "language": "{lead_language}"
}}"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": lang_config['system'] + " Always respond with valid JSON only."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=600
        )
        
        content = response.choices[0].message.content.strip()
        if content.startswith('```'):
            content = content.split('```')[1]
            if content.startswith('json'):
                content = content[4:]
        
        result = json.loads(content)
        result['language'] = lead_language  # Ensure language is tracked
        return result
        
    except Exception as e:
        print(f"Error generating email: {e}")
        return {'subject': '', 'body': '', 'error': str(e), 'language': lead_language}


def run_ai_pipeline(user_id: int, keywords: list, num_leads: int = 5):
    """
    Run the complete AI-powered lead generation pipeline
    1. Generate leads with AI
    2. Score each lead
    3. Store in database
    """
    from models import db, Lead, User
    
    print(f"\n{'='*50}")
    print(f"🤖 Starting AI Lead Generation Pipeline")
    print(f"{'='*50}")
    print(f"User ID: {user_id}")
    print(f"Keywords: {keywords}")
    print(f"Generating {num_leads} leads...")
    
    # Step 1: Generate leads
    raw_leads = generate_leads_with_ai(keywords, num_leads)
    
    if not raw_leads:
        print("❌ No leads generated")
        return []
    
    created_leads = []
    
    for raw_lead in raw_leads:
        # Step 2: Score the lead
        print(f"\n→ Scoring: @{raw_lead.get('username', 'unknown')}")
        score_data = score_lead_with_ai(raw_lead)
        
        # Step 3: Create lead in database (only use fields that exist in the model)
        lead = Lead(
            user_id=user_id,
            platform=raw_lead.get('platform', 'unknown'),
            username=raw_lead.get('username', 'unknown'),
            title=raw_lead.get('title', ''),
            content=raw_lead.get('content', ''),
            post_url=raw_lead.get('post_url', ''),
            score=score_data.get('score', 5),
            urgency=score_data.get('urgency', 5),
            budget_indicator=score_data.get('budget_indicator', 'medium'),
            problem_summary=score_data.get('problem_summary', ''),
            source_created_at=datetime.utcnow(),
            source_type='ai_generated',  # Mark as AI-generated
            status='new'
        )
        
        db.session.add(lead)
        created_leads.append(lead)
        print(f"  ✓ Score: {score_data.get('score', 5)}/10 - {score_data.get('reason', '')[:50]}")
    
    db.session.commit()
    
    # Update user stats
    user = User.query.get(user_id)
    if user:
        user.leads_found_count = (user.leads_found_count or 0) + len(created_leads)
        db.session.commit()
    
    print(f"\n{'='*50}")
    print(f"✅ Pipeline complete! Created {len(created_leads)} leads")
    print(f"{'='*50}\n")
    
    return created_leads


# CLI function for testing
if __name__ == '__main__':
    import sys
    sys.path.insert(0, '.')
    
    from dotenv import load_dotenv
    from pathlib import Path
    
    # Load environment
    env_path = Path('.env')
    if not env_path.exists():
        env_path = Path('.env.local')
    load_dotenv(env_path)
    
    # Test lead generation
    print("\n🧪 Testing AI Lead Generator\n")
    
    keywords = ['lead generation', 'automation', 'cold outreach', 'B2B sales']
    
    leads = generate_leads_with_ai(keywords, num_leads=3)
    
    if leads:
        print("\nGenerated leads:")
        for i, lead in enumerate(leads, 1):
            print(f"\n{i}. @{lead['username']} on {lead['platform']}")
            print(f"   Title: {lead['title']}")
            print(f"   Urgency: {lead.get('urgency', 'N/A')}")
            
            # Score it
            score = score_lead_with_ai(lead)
            print(f"   AI Score: {score.get('score', 'N/A')}/10")
            
            # Generate email
            email = generate_email_with_ai(lead)
            print(f"   Email Subject: {email.get('subject', 'N/A')}")
