"""
Lead Finder AI - Real Scraper Module
=====================================
Scrapes leads from Reddit (JSON endpoints), Hacker News, and Indie Hackers.
Uses polite scraping with jitter and User-Agent rotation.

Strategy: MVP validation with $0 API costs.
- Reddit: Public JSON endpoints (no OAuth required)
- Hacker News: Firebase API + BeautifulSoup
- Indie Hackers: BeautifulSoup scraping

For scaling beyond 50+ customers, consider migrating to official APIs.
"""
import os
import re
import time
import random
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from dataclasses import dataclass, field
from urllib.parse import quote_plus

import requests
from bs4 import BeautifulSoup

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# =============================================================================
# USER-AGENT ROTATION for polite scraping
# =============================================================================
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:121.0) Gecko/20100101 Firefox/121.0",
]


@dataclass
class RawLead:
    """Raw lead data from scraping"""
    username: str
    platform: str
    title: str
    content: str
    post_url: str
    external_id: str = ""
    source: str = ""  # subreddit name, 'Show HN', etc.
    language: str = "en"  # ISO language code: en, es, pt, fr
    profile_url: Optional[str] = None
    email: Optional[str] = None
    source_created_at: Optional[datetime] = None
    engagement_score: int = 0
    num_comments: int = 0


# =============================================================================
# POLITE GET - Rate-limited requests with jitter
# =============================================================================
def polite_get(url: str, min_sleep: float = 3.0, max_sleep: float = 8.0, 
               timeout: int = 15) -> Optional[requests.Response]:
    """
    Make a polite HTTP GET request with:
    - Random User-Agent rotation
    - Random delay (jitter) between requests
    - Error handling and logging
    """
    headers = {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "application/json, text/html, */*",
        "Accept-Language": "en-US,en;q=0.9,es;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
    }
    
    try:
        logger.info(f"GET {url[:100]}...")
        resp = requests.get(url, headers=headers, timeout=timeout)
        resp.raise_for_status()
    except requests.exceptions.Timeout:
        logger.error(f"Timeout fetching {url}")
        return None
    except requests.exceptions.HTTPError as e:
        logger.error(f"HTTP Error {e.response.status_code} for {url}")
        return None
    except Exception as e:
        logger.error(f"Error GET {url}: {e}")
        return None
    
    # Polite delay with jitter
    sleep_time = random.uniform(min_sleep, max_sleep)
    logger.debug(f"Sleeping {sleep_time:.2f}s for rate limiting...")
    time.sleep(sleep_time)
    
    return resp


# =============================================================================
# REDDIT SCRAPER (JSON Endpoints - No Auth Required)
# =============================================================================

# =============================================================================
# MULTI-LANGUAGE CONFIGURATION
# =============================================================================
SUBREDDITS_BY_LANGUAGE = {
    "en": ["Entrepreneur", "startups", "smallbusiness", "GrowthHacking", "SaaS", 
           "marketing", "digital_marketing", "freelance", "webdev", "sideproject"],
    "es": ["Emprendedores", "mexico", "Colombia", "argentina", "es", 
           "MexicoFinanciero", "chileemprendedores"],
    "pt": ["Empreendedorismo", "brasil", "investimentos", "brdev", 
           "startups_br", "foradacasinha"],
    "fr": ["Entrepreneur_FR", "France", "besoindeparler", "vosfinances", 
           "startups_fr", "freelance_FR"]
}

KEYWORDS_BY_LANGUAGE = {
    "en": [
        "cold email", "lead generation", "B2B growth", "need clients", 
        "looking for customers", "struggling with sales", "need help with",
        "looking for developer", "automation", "SaaS", "how do I"
    ],
    "es": [
        "email frío", "generación de leads", "necesito clientes", "busco clientes", 
        "crecimiento B2B", "ventas B2B", "automatización", "emprendimiento",
        "cómo puedo", "alguien sabe", "recomendaciones para"
    ],
    "pt": [
        "geração de leads", "preciso clientes", "email frio", "crescimento B2B",
        "procuro clientes", "vendas B2B", "automação", "empreendedorismo",
        "como posso", "alguém sabe", "recomendações para"
    ],
    "fr": [
        "génération de leads", "besoin clients", "email froid", "croissance B2B",
        "cherche clients", "ventes B2B", "automatisation", "entrepreneuriat",
        "comment puis-je", "quelqu'un sait", "recommandations pour"
    ]
}

# Language display names and flags
LANGUAGE_INFO = {
    "en": {"name": "English", "flag": "🇬🇧", "display": "EN"},
    "es": {"name": "Español", "flag": "🇪🇸", "display": "ES"},
    "pt": {"name": "Português", "flag": "🇧🇷", "display": "PT"},
    "fr": {"name": "Français", "flag": "🇫🇷", "display": "FR"},
}


class RedditJSONScraper:
    """
    Scrape Reddit using public JSON endpoints.
    
    Example URL:
    https://www.reddit.com/r/Entrepreneur/search.json?q=looking+for+developer&restrict_sr=on&sort=new&limit=10
    
    Advantages:
    - No OAuth required
    - Free access
    - Returns structured JSON
    - Multi-language support (EN, ES, PT, FR)
    
    Limitations:
    - Rate limited by Reddit
    - May get blocked with aggressive scraping
    """
    
    # Default subreddits (English) for backwards compatibility
    SUBREDDITS = SUBREDDITS_BY_LANGUAGE.get("en", [])
    
    def __init__(self):
        pass
    
    def scrape_subreddit_search(self, subreddit: str, query: str, 
                                 limit: int = 10) -> List[Dict]:
        """
        Search a subreddit for posts matching query.
        Returns list of dicts with: title, url, score, num_comments, author, selftext, id
        """
        encoded_query = quote_plus(query)
        url = f"https://www.reddit.com/r/{subreddit}/search.json?q={encoded_query}&restrict_sr=on&sort=new&limit={limit}"
        
        resp = polite_get(url)
        if not resp:
            return []
        
        try:
            data = resp.json()
            posts = data.get('data', {}).get('children', [])
            
            results = []
            for post_wrapper in posts:
                post = post_wrapper.get('data', {})
                if not post:
                    continue
                
                results.append({
                    'id': post.get('id', ''),
                    'title': post.get('title', ''),
                    'url': f"https://reddit.com{post.get('permalink', '')}",
                    'score': post.get('score', 0),
                    'num_comments': post.get('num_comments', 0),
                    'author': post.get('author', '[deleted]'),
                    'selftext': post.get('selftext', '')[:2000],
                    'created_utc': post.get('created_utc', 0),
                    'subreddit': subreddit,
                })
            
            logger.info(f"Reddit r/{subreddit} search '{query}': {len(results)} posts")
            return results
            
        except Exception as e:
            logger.error(f"Error parsing Reddit JSON: {e}")
            return []
    
    def scrape_subreddit_new(self, subreddit: str, limit: int = 10) -> List[Dict]:
        """
        Get newest posts from a subreddit.
        """
        url = f"https://www.reddit.com/r/{subreddit}/new.json?limit={limit}"
        
        resp = polite_get(url)
        if not resp:
            return []
        
        try:
            data = resp.json()
            posts = data.get('data', {}).get('children', [])
            
            results = []
            for post_wrapper in posts:
                post = post_wrapper.get('data', {})
                if not post:
                    continue
                
                results.append({
                    'id': post.get('id', ''),
                    'title': post.get('title', ''),
                    'url': f"https://reddit.com{post.get('permalink', '')}",
                    'score': post.get('score', 0),
                    'num_comments': post.get('num_comments', 0),
                    'author': post.get('author', '[deleted]'),
                    'selftext': post.get('selftext', '')[:2000],
                    'created_utc': post.get('created_utc', 0),
                    'subreddit': subreddit,
                })
            
            logger.info(f"Reddit r/{subreddit}/new: {len(results)} posts")
            return results
            
        except Exception as e:
            logger.error(f"Error parsing Reddit JSON: {e}")
            return []
    
    def scrape(self, keywords: List[str], subreddits: List[str] = None, 
               limit_per_sub: int = 5, max_requests: int = 20,
               language: str = "en") -> List[RawLead]:
        """
        Main scraping method. Searches keywords across subreddits.
        
        Args:
            keywords: List of keywords to search for
            subreddits: List of subreddits to search (default: English subreddits)
            limit_per_sub: Max posts per subreddit
            max_requests: Max HTTP requests
            language: ISO language code (en, es, pt, fr) - used to tag leads
        """
        leads = []
        subs_to_scrape = subreddits or self.SUBREDDITS[:7]  # Limit default subreddits
        request_count = 0
        
        for subreddit in subs_to_scrape:
            if request_count >= max_requests:
                logger.warning(f"Reached max requests ({max_requests}), stopping Reddit scrape")
                break
            
            # Search with each keyword
            for keyword in keywords[:3]:  # Limit keywords per cycle
                if request_count >= max_requests:
                    break
                
                posts = self.scrape_subreddit_search(subreddit, keyword, limit=limit_per_sub)
                request_count += 1
                
                for post in posts:
                    lead = RawLead(
                        username=post['author'],
                        platform='reddit',
                        title=post['title'],
                        content=post['selftext'] if post['selftext'] else post['title'],
                        post_url=post['url'],
                        external_id=post['id'],
                        source=f"r/{post['subreddit']}",
                        language=language,  # Track language
                        profile_url=f"https://reddit.com/user/{post['author']}" if post['author'] != '[deleted]' else None,
                        source_created_at=datetime.fromtimestamp(post['created_utc']) if post['created_utc'] else None,
                        engagement_score=post['score'] + post['num_comments'],
                        num_comments=post['num_comments'],
                    )
                    leads.append(lead)
        
        logger.info(f"Reddit [{language.upper()}]: {len(leads)} leads from {request_count} requests")
        return leads
    
    def scrape_multilang(
        self,
        languages: List[str] = None,
        limit_per_sub: int = 5,
        max_requests_per_lang: int = 10
    ) -> List[RawLead]:
        """
        Scrape Reddit across multiple languages.
        
        Args:
            languages: List of language codes to scrape (default: all configured)
            limit_per_sub: Max posts per subreddit
            max_requests_per_lang: Max HTTP requests per language
            
        Returns:
            List of RawLead with language attribute set
        """
        all_leads = []
        langs_to_scrape = languages or list(SUBREDDITS_BY_LANGUAGE.keys())
        
        for lang in langs_to_scrape:
            logger.info(f"\n{'='*40}")
            logger.info(f"Scraping Reddit in {LANGUAGE_INFO.get(lang, {}).get('name', lang).upper()}")
            logger.info(f"{'='*40}")
            
            subreddits = SUBREDDITS_BY_LANGUAGE.get(lang, [])
            keywords = KEYWORDS_BY_LANGUAGE.get(lang, [])
            
            if not subreddits:
                logger.warning(f"No subreddits configured for language: {lang}")
                continue
            
            leads = self.scrape(
                keywords=keywords,
                subreddits=subreddits[:5],  # Limit subreddits per language
                limit_per_sub=limit_per_sub,
                max_requests=max_requests_per_lang,
                language=lang
            )
            all_leads.extend(leads)
        
        logger.info(f"\nReddit Multi-Lang Total: {len(all_leads)} leads across {len(langs_to_scrape)} languages")
        return all_leads


# =============================================================================
# HACKER NEWS SCRAPER
# =============================================================================
class HackerNewsScraper:
    """
    Scrape Hacker News using Firebase API + BeautifulSoup for Show HN/Ask HN.
    """
    
    API_BASE = "https://hacker-news.firebaseio.com/v0"
    WEB_BASE = "https://news.ycombinator.com"
    
    def __init__(self):
        pass
    
    def scrape_show_hn(self, limit: int = 10) -> List[Dict]:
        """
        Scrape Show HN stories from the web page.
        Show HN = people launching projects = potential customers
        """
        url = f"{self.WEB_BASE}/show"
        resp = polite_get(url, min_sleep=2, max_sleep=5)
        if not resp:
            return []
        
        try:
            soup = BeautifulSoup(resp.text, 'html.parser')
            items = soup.select('tr.athing')[:limit]
            
            results = []
            for item in items:
                try:
                    story_id = item.get('id', '')
                    title_elem = item.select_one('span.titleline > a')
                    title = title_elem.get_text(strip=True) if title_elem else ''
                    link = title_elem.get('href', '') if title_elem else ''
                    
                    # Get metadata from next row
                    subtext = item.find_next_sibling('tr')
                    score_elem = subtext.select_one('span.score') if subtext else None
                    score = int(score_elem.get_text().replace(' points', '')) if score_elem else 0
                    
                    author_elem = subtext.select_one('a.hnuser') if subtext else None
                    author = author_elem.get_text(strip=True) if author_elem else 'unknown'
                    
                    comments_elem = subtext.select('a')[-1] if subtext else None
                    comments_text = comments_elem.get_text() if comments_elem else '0'
                    num_comments = int(re.search(r'(\d+)', comments_text).group(1)) if re.search(r'(\d+)', comments_text) else 0
                    
                    results.append({
                        'id': story_id,
                        'title': title,
                        'url': f"{self.WEB_BASE}/item?id={story_id}",
                        'external_link': link,
                        'score': score,
                        'num_comments': num_comments,
                        'author': author,
                        'type': 'Show HN',
                    })
                except Exception as e:
                    logger.debug(f"Error parsing HN item: {e}")
                    continue
            
            logger.info(f"HN Show HN: {len(results)} stories")
            return results
            
        except Exception as e:
            logger.error(f"Error scraping Show HN: {e}")
            return []
    
    def scrape_ask_hn(self, limit: int = 10) -> List[Dict]:
        """
        Scrape Ask HN stories - people asking questions = pain points
        """
        url = f"{self.WEB_BASE}/ask"
        resp = polite_get(url, min_sleep=2, max_sleep=5)
        if not resp:
            return []
        
        try:
            soup = BeautifulSoup(resp.text, 'html.parser')
            items = soup.select('tr.athing')[:limit]
            
            results = []
            for item in items:
                try:
                    story_id = item.get('id', '')
                    title_elem = item.select_one('span.titleline > a')
                    title = title_elem.get_text(strip=True) if title_elem else ''
                    
                    subtext = item.find_next_sibling('tr')
                    score_elem = subtext.select_one('span.score') if subtext else None
                    score = int(score_elem.get_text().replace(' points', '')) if score_elem else 0
                    
                    author_elem = subtext.select_one('a.hnuser') if subtext else None
                    author = author_elem.get_text(strip=True) if author_elem else 'unknown'
                    
                    results.append({
                        'id': story_id,
                        'title': title,
                        'url': f"{self.WEB_BASE}/item?id={story_id}",
                        'score': score,
                        'num_comments': 0,
                        'author': author,
                        'type': 'Ask HN',
                    })
                except Exception as e:
                    logger.debug(f"Error parsing HN Ask item: {e}")
                    continue
            
            logger.info(f"HN Ask HN: {len(results)} stories")
            return results
            
        except Exception as e:
            logger.error(f"Error scraping Ask HN: {e}")
            return []
    
    def scrape(self, keywords: List[str] = None, limit: int = 10) -> List[RawLead]:
        """
        Main scraping method for HN. Gets Show HN and Ask HN.
        """
        leads = []
        
        # Get Show HN (people launching products)
        show_stories = self.scrape_show_hn(limit=limit)
        for story in show_stories:
            lead = RawLead(
                username=story['author'],
                platform='hackernews',
                title=story['title'],
                content=story['title'],  # HN titles are usually descriptive
                post_url=story['url'],
                external_id=story['id'],
                source=story['type'],
                profile_url=f"{self.WEB_BASE}/user?id={story['author']}",
                engagement_score=story['score'] + story['num_comments'],
                num_comments=story['num_comments'],
            )
            leads.append(lead)
        
        # Get Ask HN (people with questions/problems)
        ask_stories = self.scrape_ask_hn(limit=limit)
        for story in ask_stories:
            # Filter by keywords if provided
            if keywords:
                title_lower = story['title'].lower()
                if not any(kw.lower() in title_lower for kw in keywords):
                    continue
            
            lead = RawLead(
                username=story['author'],
                platform='hackernews',
                title=story['title'],
                content=story['title'],
                post_url=story['url'],
                external_id=story['id'],
                source=story['type'],
                profile_url=f"{self.WEB_BASE}/user?id={story['author']}",
                engagement_score=story['score'],
                num_comments=story.get('num_comments', 0),
            )
            leads.append(lead)
        
        logger.info(f"HN total: {len(leads)} leads")
        return leads


# =============================================================================
# INDIE HACKERS SCRAPER
# =============================================================================
class IndieHackersScraper:
    """
    Scrape Indie Hackers for potential leads.
    """
    
    BASE_URL = "https://www.indiehackers.com"
    
    def __init__(self):
        pass
    
    def scrape_feed(self, limit: int = 10) -> List[Dict]:
        """
        Scrape the Indie Hackers feed/home for recent posts.
        """
        # Try the main page
        resp = polite_get(self.BASE_URL, min_sleep=3, max_sleep=6)
        if not resp:
            return []
        
        try:
            soup = BeautifulSoup(resp.text, 'html.parser')
            
            # Look for posts in various possible selectors
            posts = []
            
            # Try finding feed items
            feed_items = soup.select('.feed-item, .post-card, article, .ember-view.post')[:limit]
            
            for item in feed_items:
                try:
                    # Try multiple selectors for title
                    title_elem = item.select_one('h2, h3, .title, .post-title, a.feed-item__title')
                    title = title_elem.get_text(strip=True) if title_elem else ''
                    if not title:
                        continue
                    
                    # Try to get link
                    link_elem = item.select_one('a[href*="/post/"], a[href*="/product/"]')
                    link = link_elem.get('href', '') if link_elem else ''
                    if link and not link.startswith('http'):
                        link = f"{self.BASE_URL}{link}"
                    
                    # Try to get author
                    author_elem = item.select_one('.author, .username, .user-link')
                    author = author_elem.get_text(strip=True) if author_elem else 'unknown'
                    
                    # Try to get content/summary
                    content_elem = item.select_one('.content, .body, .excerpt, p')
                    content = content_elem.get_text(strip=True)[:500] if content_elem else ''
                    
                    if title:
                        posts.append({
                            'title': title,
                            'url': link or f"{self.BASE_URL}",
                            'author': author,
                            'content': content or title,
                        })
                except Exception as e:
                    logger.debug(f"Error parsing IH item: {e}")
                    continue
            
            logger.info(f"Indie Hackers: {len(posts)} posts found")
            return posts
            
        except Exception as e:
            logger.error(f"Error scraping Indie Hackers: {e}")
            return []
    
    def scrape(self, keywords: List[str] = None, limit: int = 10) -> List[RawLead]:
        """
        Main scraping method for Indie Hackers.
        """
        leads = []
        
        posts = self.scrape_feed(limit=limit)
        
        for idx, post in enumerate(posts):
            # Filter by keywords if provided
            if keywords:
                text = f"{post['title']} {post.get('content', '')}".lower()
                if not any(kw.lower() in text for kw in keywords):
                    continue
            
            lead = RawLead(
                username=post['author'],
                platform='indiehackers',
                title=post['title'],
                content=post.get('content', post['title']),
                post_url=post['url'],
                external_id=f"ih_{idx}_{hash(post['title']) % 10000}",
                source='Indie Hackers Feed',
                engagement_score=0,  # IH doesn't show engagement easily
            )
            leads.append(lead)
        
        logger.info(f"Indie Hackers total: {len(leads)} leads")
        return leads


# =============================================================================
# MULTI-PLATFORM SCRAPER (Orchestrator)
# =============================================================================
class MultiPlatformScraper:
    """
    Orchestrates scraping across all platforms with filtering.
    """
    
    def __init__(self, min_engagement: int = 2, max_requests: int = 20):
        """
        Args:
            min_engagement: Minimum engagement score (upvotes + comments) to keep a lead
            max_requests: Maximum HTTP requests per scraping cycle
        """
        self.min_engagement = min_engagement
        self.max_requests = max_requests
        
        self.scrapers = {
            'reddit': RedditJSONScraper(),
            'hackernews': HackerNewsScraper(),
            'indiehackers': IndieHackersScraper(),
        }
    
    def filter_by_keywords(self, leads: List[RawLead], keywords: List[str]) -> List[RawLead]:
        """
        Filter leads that match at least one keyword.
        """
        if not keywords:
            return leads
        
        filtered = []
        for lead in leads:
            text = f"{lead.title} {lead.content}".lower()
            if any(kw.lower() in text for kw in keywords):
                filtered.append(lead)
        
        logger.info(f"Keyword filter: {len(leads)} -> {len(filtered)} leads")
        return filtered
    
    def filter_by_engagement(self, leads: List[RawLead], min_score: int = None) -> List[RawLead]:
        """
        Filter leads by minimum engagement score.
        """
        threshold = min_score if min_score is not None else self.min_engagement
        
        # For Indie Hackers, we can't filter by engagement (no scores)
        filtered = [
            lead for lead in leads 
            if lead.platform == 'indiehackers' or lead.engagement_score >= threshold
        ]
        
        logger.info(f"Engagement filter (>={threshold}): {len(leads)} -> {len(filtered)} leads")
        return filtered
    
    def deduplicate(self, leads: List[RawLead]) -> List[RawLead]:
        """
        Remove duplicate leads based on external_id or content fingerprint.
        """
        seen = set()
        unique = []
        
        for lead in leads:
            # Use external_id if available, otherwise content fingerprint
            if lead.external_id:
                key = f"{lead.platform}:{lead.external_id}"
            else:
                key = f"{lead.platform}:{lead.username}:{lead.title[:50]}"
            
            if key not in seen:
                seen.add(key)
                unique.append(lead)
        
        logger.info(f"Deduplication: {len(leads)} -> {len(unique)} leads")
        return unique
    
    def scrape_all(
        self, 
        keywords: List[str], 
        platforms: List[str] = None,
        limit_per_platform: int = 10,
        language: str = "en"
    ) -> List[RawLead]:
        """
        Scrape all enabled platforms and return filtered, deduplicated leads.
        
        Args:
            keywords: Keywords to search for
            platforms: List of platforms to scrape
            limit_per_platform: Max leads per platform
            language: Language for Reddit scraping (en, es, pt, fr)
        """
        all_leads = []
        platforms_to_scrape = platforms or ['reddit', 'hackernews', 'indiehackers']
        
        for platform in platforms_to_scrape:
            if platform not in self.scrapers:
                logger.warning(f"Unknown platform: {platform}")
                continue
            
            logger.info(f"\n{'='*50}")
            logger.info(f"Scraping {platform.upper()} [{language.upper()}]...")
            logger.info(f"{'='*50}")
            
            try:
                scraper = self.scrapers[platform]
                
                if platform == 'reddit':
                    leads = scraper.scrape(
                        keywords=keywords, 
                        limit_per_sub=min(5, limit_per_platform),
                        max_requests=self.max_requests,
                        language=language
                    )
                else:
                    leads = scraper.scrape(keywords=keywords, limit=limit_per_platform)
                    # HN and IH are English-only platforms
                    if language == "en":
                        all_leads.extend(leads)
                        logger.info(f"Got {len(leads)} leads from {platform}")
                    continue
                
                all_leads.extend(leads)
                logger.info(f"Got {len(leads)} leads from {platform}")
                
            except Exception as e:
                logger.error(f"Error scraping {platform}: {e}")
                continue
        
        # Apply filters
        filtered = self.filter_by_keywords(all_leads, keywords)
        filtered = self.filter_by_engagement(filtered)
        unique = self.deduplicate(filtered)
        
        # Sort by engagement (highest first)
        unique.sort(key=lambda x: x.engagement_score, reverse=True)
        
        logger.info(f"\n{'='*50}")
        logger.info(f"TOTAL: {len(unique)} unique leads after filtering")
        logger.info(f"{'='*50}\n")
        
        return unique
    
    def scrape_all_multilang(
        self,
        platforms: List[str] = None,
        languages: List[str] = None,
        limit_per_platform: int = 10
    ) -> List[RawLead]:
        """
        Scrape all platforms across multiple languages.
        
        Args:
            platforms: List of platforms to scrape
            languages: List of language codes (default: all configured)
            limit_per_platform: Max leads per platform per language
            
        Returns:
            List of RawLead with language attribute set
        """
        all_leads = []
        langs_to_scrape = languages or list(SUBREDDITS_BY_LANGUAGE.keys())
        platforms_to_scrape = platforms or ['reddit', 'hackernews', 'indiehackers']
        
        logger.info(f"\n{'='*60}")
        logger.info(f"  MULTI-LANGUAGE SCRAPING: {len(langs_to_scrape)} languages")
        logger.info(f"  Languages: {', '.join([LANGUAGE_INFO.get(l, {}).get('name', l) for l in langs_to_scrape])}")
        logger.info(f"  Platforms: {', '.join(platforms_to_scrape)}")
        logger.info(f"{'='*60}\n")
        
        for lang in langs_to_scrape:
            lang_info = LANGUAGE_INFO.get(lang, {"name": lang, "flag": ""})
            logger.info(f"\n{lang_info['flag']} Processing {lang_info['name'].upper()}...")
            
            keywords = KEYWORDS_BY_LANGUAGE.get(lang, KEYWORDS_BY_LANGUAGE.get("en", []))
            
            for platform in platforms_to_scrape:
                if platform not in self.scrapers:
                    continue
                
                try:
                    scraper = self.scrapers[platform]
                    
                    if platform == 'reddit':
                        # Use language-specific subreddits and keywords
                        subreddits = SUBREDDITS_BY_LANGUAGE.get(lang, [])
                        if not subreddits:
                            continue
                        
                        leads = scraper.scrape(
                            keywords=keywords[:3],
                            subreddits=subreddits[:4],
                            limit_per_sub=min(3, limit_per_platform),
                            max_requests=max(5, self.max_requests // len(langs_to_scrape)),
                            language=lang
                        )
                        all_leads.extend(leads)
                        logger.info(f"  → Reddit [{lang}]: {len(leads)} leads")
                        
                    elif lang == "en":
                        # HN and IH are primarily English
                        leads = scraper.scrape(keywords=keywords, limit=limit_per_platform)
                        for lead in leads:
                            lead.language = "en"
                        all_leads.extend(leads)
                        logger.info(f"  → {platform.title()}: {len(leads)} leads")
                        
                except Exception as e:
                    logger.error(f"Error scraping {platform} [{lang}]: {e}")
                    continue
        
        # Apply filters and deduplication
        filtered = self.filter_by_engagement(all_leads)
        unique = self.deduplicate(filtered)
        unique.sort(key=lambda x: x.engagement_score, reverse=True)
        
        # Summary by language
        lang_counts = {}
        for lead in unique:
            lang_counts[lead.language] = lang_counts.get(lead.language, 0) + 1
        
        logger.info(f"\n{'='*60}")
        logger.info(f"  MULTI-LANG SCRAPING COMPLETE")
        logger.info(f"  Total: {len(unique)} unique leads")
        for lang, count in sorted(lang_counts.items()):
            info = LANGUAGE_INFO.get(lang, {"flag": "", "name": lang})
            logger.info(f"    {info['flag']} {info['name']}: {count} leads")
        logger.info(f"{'='*60}\n")
        
        return unique


# =============================================================================
# STANDALONE TEST
# =============================================================================
if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv('.env.local')
    
    # Test scraping
    scraper = MultiPlatformScraper(min_engagement=2, max_requests=10)
    
    keywords = [
        'looking for developer',
        'need help with',
        'struggling with',
        'recommendations for',
        'automation',
        'SaaS',
        'startup',
    ]
    
    leads = scraper.scrape_all(
        keywords=keywords,
        platforms=['hackernews', 'reddit'],  # Test subset
        limit_per_platform=5
    )
    
    print(f"\n{'='*60}")
    print(f"RESULTS: {len(leads)} leads found")
    print(f"{'='*60}")
    
    for lead in leads[:10]:
        print(f"\n[{lead.platform.upper()}] @{lead.username}")
        print(f"  Source: {lead.source}")
        print(f"  Score: {lead.engagement_score}")
        print(f"  Title: {lead.title[:80]}...")
        print(f"  URL: {lead.post_url}")
