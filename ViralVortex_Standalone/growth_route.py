# Creado por: Director de Crecimiento (Loki + Data-Driven)
import os
from engine import ViralVortexEngine
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '.env.local'))

def self_promote():
    """
    Script de promoción para Viral Vortex.
    Usa el motor para vender el propio motor.
    """
    engine = ViralVortexEngine()
    
    # Campaña para atraer usuarios de Reddit (r/sideproject)
    topic = (
        "How I built an AI agent that analyzes the science of virality (Jonah Berger's STEPPS) "
        "and humanizes content to beat Reddit's spam filters."
    )
    
    engine.run_campaign(
        topic=topic,
        persona_name="CryptoSkeptic_Dave",
        community="r/sideproject"
    )

if __name__ == "__main__":
    print("--- INICIANDO RUTA DE CRECIMIENTO AUTÓNOMO ---")
    self_promote()
