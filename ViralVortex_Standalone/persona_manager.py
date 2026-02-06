import os
import uuid
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '.env.local'))

class PersonaManager:
    """
    Manages Viral Vortex personas and their long-term memory.
    Implements Supervisor Order #4: Multi-Persona Mesh with RAG capability.
    """
    
    def __init__(self):
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_KEY")
        self.supabase: Client = create_client(url, key)

    def create_persona(self, name, backstory, tone, slang=[], platforms=["reddit", "twitter"]):
        """Creates a new persistent persona."""
        data = {
            "name": name,
            "backstory": backstory,
            "tone": tone,
            "slang_preferences": slang,
            "target_platforms": platforms
        }
        result = self.supabase.table("personas").insert(data).execute()
        return result.data[0]

    def get_personas(self):
        """Retrieves all active personas."""
        result = self.supabase.table("personas").select("*").execute()
        return result.data

    def record_content(self, persona_id, content, platform, score, embedding=None, video_url=None):
        """Records a post in the history to enable long-term memory."""
        data = {
            "persona_id": persona_id,
            "content": content,
            "platform": platform,
            "virality_score": score,
            "embedding": embedding,
            "video_url": video_url
        }
        result = self.supabase.table("content_history").insert(data).execute()
        return result.data[0]

    def get_persona_memory(self, persona_id, limit=5):
        """Retrieves recent history for a persona to maintain consistency."""
        result = self.supabase.table("content_history") \
            .select("content") \
            .eq("persona_id", persona_id) \
            .order("created_at", desc=True) \
            .limit(limit) \
            .execute()
        return [item['content'] for item in result.data]

if __name__ == "__main__":
    pm = PersonaManager()
    
    # Create a demo persona
    demo = pm.create_persona(
        name="CryptoSkeptic_Dave",
        backstory="A cynical software engineer from Berlin who hates hype but loves tech.",
        tone="Cynical, analytical, uses 'bro' ironically.",
        slang=["rekt", "classic", "stablecoin-fail", "cope"],
        platforms=["reddit", "twitter"]
    )
    print(f"Created Persona: {demo['name']} (ID: {demo['id']})")
    
    # Record first activity
    pm.record_content(
        persona_id=demo['id'],
        content="Just saw another 'AI will save the world' post. Bro, it's just a linear regression on steroids. Cope harder.",
        platform="reddit",
        score=8.5
    )
    print("Recorded historical memory for consistency.")
