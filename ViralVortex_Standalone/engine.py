import os
import json
from humanizer import Humanizer
from stepps_evaluator import STEPPSEvaluator
from persona_manager import PersonaManager
from sentinel import Sentinel
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '.env.local'))

class ViralVortexEngine:
    """
    The main orchestrator for Viral Vortex.
    Coordinates Research, Perfection, and Autonomous Execution.
    """
    
    def __init__(self):
        self.humanizer = Humanizer()
        self.evaluator = STEPPSEvaluator()
        self.persona_manager = PersonaManager()
        self.sentinel = Sentinel()

    def run_campaign(self, topic, persona_name=None, platform="reddit", community="r/test", is_pro=True, language="es"):
        print(f"🚀 Starting Viral Campaign [PRO]: '{topic}' on {platform}/{community} [{language.upper()}]")
        
        # 1. Select Persona
        personas = self.persona_manager.get_personas()
        persona = next((p for p in personas if p['name'] == persona_name), personas[0])
        print(f"👤 Acting as: {persona['name']}")
        
        # 2. Vibe Check (Sentinel)
        is_safe, sentiment = self.sentinel.check_community_vibe(platform, community)
        if not is_safe:
            print(f"🛑 ABORT: Community {community} is currently too toxic (Sentiment: {sentiment:.2f})")
            return
        
        # 3. Generate & Humanize (Perfection Layer)
        raw_content = self.humanizer.generate_viral_draft(topic, language=language)
        human_content = self.humanizer.humanize(raw_content, platform, language=language)
        
        # 4. Evaluate (Science Layer)
        rating = self.evaluator.evaluate(human_content)
        print(f"📊 Virality Score: {rating['total_score']}/10")
        
        if rating['total_score'] < 7.0:
            print(f"⚠️ Content rejected by STEPPS Evaluator: {rating['feedback']}")
            return

        # 5. Pro Feature: Wan 2.1 Video Generation
        if is_pro:
            from video_gen import VideoGenerator
            vg = VideoGenerator()
            video = vg.generate_video(f"Viral clip for: {topic}")
            video_url = video['video_url'] # Assign video_url
            print(f"🎬 PRO: Attached Wan 2.1 Video -> {video_url}")

        # 6. Execute (Mocked for safety)
        print(f"✅ EXECUTION: Posting to {community}...")
        print(f"\n--- CONTENT ---\n{human_content}\n---------------")
        
        # 7. Record Memory
        self.persona_manager.record_content(
            persona_id=persona['id'],
            content=human_content,
            platform=platform,
            score=rating['total_score'],
            video_url=video_url
        )
        print(f"📌 Memory Synchronized. Video: {video_url}")
        
        # 7. Post-Launch Sentinel
        time_to_wait = 1  # In production: 900 (15 min)
        visible = self.sentinel.verify_post_visibility("mock_id_123")
        if visible:
            print("🌟 MISSION SUCCESS: Post is live and tracking.")
        else:
            print("❌ MISSION FAILED: Post deleted or hidden.")

if __name__ == "__main__":
    engine = ViralVortexEngine()
    engine.run_campaign(
        topic="How to build a SaaS in 24 hours with AI in 2026",
        persona_name="CryptoSkeptic_Dave",
        community="r/saas"
    )
