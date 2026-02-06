import os
import time
import random
from engine import ViralVortexEngine
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '.env.local'))

class MarketingOrchestrator:
    """
    Fulfills the 'Engineer as Marketing' autonomous strategy.
    The goal is to use the Viral Vortex Engine to promote the 
    Viral Vortex Checker tool without human intervention.
    """
    
    def __init__(self):
        self.engine = ViralVortexEngine()
        # The URL of your free tool (Checker)
        self.checker_url = "http://localhost:5001/" 

    def generate_marketing_bait(self, language="es"):
        """
        Creates 'bait' content designed to make people curious 
        about their own content's virality.
        """
        baits_es = [
            "Analicé los 100 mejores posts de Reddit de 2026. La mayoría falla en 'Moneda Social'. Prueba esta herramienta gratis: {url}",
            "Deja de publicar contenido de IA perfecto. Reddit te está baneando. Este analizador te dice si pareces un bot: {url}",
            "¿Por qué unos posts explotan y otros mueren? Es el marco STEPPS. Mira tu score gratis: {url}"
        ]
        baits_en = [
            "I analyzed the top 100 Reddit posts of 2026 using science. Most of you are failing at 'Social Currency'. Try this free tool to check your score: {url}",
            "Stop posting 'perfect' AI content. Reddit is banning you. Here is a checker that tells you if your post looks like a bot: {url}",
            "Why do some posts blow up while others die? It's not luck, it's the STEPPS framework. Check your score for free: {url}"
        ]
        baits = baits_es if language == "es" else baits_en
        return random.choice(baits).format(url=self.checker_url)

    def run_autonomous_growth(self):
        """
        The Infinite Loop: 
        1. Pick a community.
        2. Check the vibe (Sentinel).
        3. Generate bait.
        4. Post it using a specific Persona.
        5. Verify visibility.
        """
        targets = [
            {"platform": "reddit", "community": "r/sideproject", "lang": "en"},
            {"platform": "reddit", "community": "r/saas", "lang": "en"},
            {"platform": "reddit", "community": "r/emprendedores", "lang": "es"},
            {"platform": "twitter", "community": "AI_Automation", "lang": "en"}
        ]
        
        target = random.choice(targets)
        topic = self.generate_marketing_bait(language=target['lang'])
        
        print(f"🔄 [GROWTH LOOP] Attempting autonomous promotion on {target['community']} [{target['lang'].upper()}]")
        
        persona = "Global_Mark" if target['lang'] == "en" else "CryptoSkeptic_Dave"
        
        self.engine.run_campaign(
            topic=topic,
            persona_name=persona,
            platform=target['platform'],
            community=target['community'],
            is_pro=False, # Lean launch: text only for baits
            language=target['lang']
        )

if __name__ == "__main__":
    orchestrator = MarketingOrchestrator()
    
    # This would run on a schedule (e.g. every 12 hours)
    while True:
        orchestrator.run_autonomous_growth()
        
        # Wait for a random interval to mimic human behavior (e.g. 8 to 14 hours)
        wait_time = random.randint(8*3600, 14*3600)
        print(f"💤 Sleeping for {wait_time/3600:.1f} hours to maintain human mimicry...")
        time.sleep(wait_time)
