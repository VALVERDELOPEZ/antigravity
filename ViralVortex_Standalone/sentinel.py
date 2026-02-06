import os
import random
import time
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '.env.local'))

class Sentinel:
    """
    Fulfills Supervisor Order #3: Sentiment Monitoring and Shadowban Sentinel.
    Protects automation by performing 'vibe checks'.
    """
    
    def __init__(self):
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_KEY")
        self.supabase: Client = create_client(url, key)

    def check_community_vibe(self, platform, community):
        """
        Simulates checking if a community is currently 'hot' or 'hostile'.
        In production, this would scrape the latest 10 posts.
        """
        # TODO: Implement real-time scraping integration
        sentiment = random.uniform(-1, 1) # Mock sentiment
        is_safe = sentiment > -0.3 # If too toxic, don't post
        
        data = {
            "platform": platform,
            "community_name": community,
            "sentiment_score": sentiment,
            "is_safe_to_post": is_safe
        }
        self.supabase.table("community_sentiment").insert(data).execute()
        return is_safe, sentiment

    def verify_post_visibility(self, post_id_on_platform):
        """
        Fulfills the 'Sentinel' duty: Check if the post is visible 15min later.
        Prevents wasting resources on shadowbanned accounts.
        """
        print(f"Waiting 1s to verify visibility for {post_id_on_platform}... (Mocked)")
        # In a real scenario, we check the post URL from an incognito session/different proxy
        is_visible = random.choice([True, True, True, False]) # 75% success rate simulation
        return is_visible

if __name__ == "__main__":
    s = Sentinel()
    safe, score = s.check_community_vibe("reddit", "r/technology")
    print(f"Community: r/technology | Safe to post: {safe} | Sentiment: {score:.2f}")
    
    visible = s.verify_post_visibility("reddit_abc123")
    if not visible:
        print("ALERT: Post is not visible. Potential shadowban or auto-mod deletion.")
    else:
        print("Success: Post is live and visible.")
