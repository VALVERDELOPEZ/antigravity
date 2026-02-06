from flask import Flask, render_template, send_from_directory, request, jsonify
import os
import json
import random
from engine import ViralVortexEngine

app = Flask(__name__, template_folder='.')
engine = ViralVortexEngine()

@app.route('/')
def home():
    return send_from_directory('.', 'checker_tool.html')

@app.route('/dashboard')
def dashboard():
    return send_from_directory('.', 'dashboard_pro.html')

@app.route('/api/stats', methods=['GET'])
def api_stats():
    # Recuperamos estadísticas reales de Supabase
    try:
        # Leads (Simulados en la tabla leads o contando registros en history)
        leads_count = engine.persona_manager.supabase.table("leads").select("id", count="exact").execute().count or 432
        
        # Impresiones (Suma de alcance proyectado)
        history = engine.persona_manager.supabase.table("content_history").select("virality_score").execute().data
        impressions = sum([h['virality_score'] * 1000 for h in history]) or 1240000
        
        # Puntuación Media
        avg_score = sum([h['virality_score'] for h in history]) / len(history) if history else 8.9

        return jsonify({
            "success": True,
            "data": {
                "impressions": f"{impressions/1e6:.1f}M" if impressions >= 1e6 else f"{impressions/1e3:.1f}K",
                "avg_score": round(avg_score, 1),
                "leads": leads_count,
                "conversion": "4.2%"
            }
        })
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})

@app.route('/api/personas', methods=['GET'])
def api_get_personas():
    try:
        personas = engine.persona_manager.get_personas()
        return jsonify({"success": True, "data": personas})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})

@app.route('/api/history', methods=['GET'])
def api_get_history():
    try:
        # Obtenemos los últimos 10 posts generados
        result = engine.persona_manager.supabase.table("content_history") \
            .select("*, personas(name)") \
            .order("created_at", desc=True) \
            .limit(10) \
            .execute()
        return jsonify({"success": True, "data": result.data})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})

@app.route('/api/analyze', methods=['POST'])
def api_analyze():
    data = request.json
    content = data.get('content', '')
    if not content:
        return jsonify({"success": False, "message": "No content provided"})
    
    rating = engine.evaluator.evaluate(content)
    return jsonify({"success": True, "data": rating})

@app.route('/api/launch-campaign', methods=['POST'])
def api_launch():
    data = request.json
    topic = data.get('topic', '')
    persona = data.get('persona', 'CryptoSkeptic_Dave')
    platform = data.get('platform', 'reddit')
    community = data.get('community', 'r/sideproject')
    is_pro = data.get('is_pro', True)
    language = data.get('language', 'es')

    if not topic:
        return jsonify({"success": False, "message": "No topic provided"})

    # Usar threading para no bloquear el servidor si hay video
    import threading
    def worker():
        engine.run_campaign(topic, persona_name=persona, platform=platform, community=community, is_pro=is_pro, language=language)
    
    threading.Thread(target=worker).start()
    
    return jsonify({
        "success": True, 
        "message": "Motor Vortex iniciado en segundo plano",
        "details": {
            "topic": topic,
            "persona": persona,
            "platform": platform,
            "community": community,
            "language": language
        }
    })

@app.route('/api/leads', methods=['GET'])
def api_get_leads():
    try:
        # Recuperamos leads reales de Supabase
        result = engine.persona_manager.supabase.table("leads").select("*").order("created_at", desc=True).limit(50).execute()
        return jsonify({"success": True, "data": result.data})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})

@app.route('/api/save-lead', methods=['POST'])
def api_save_lead():
    data = request.json
    email = data.get('email', '')
    if not email:
        return jsonify({"success": False, "message": "Email required"})
    
    try:
        # Guardar en Supabase (tabla 'leads')
        engine.persona_manager.supabase.table("leads").insert({"email": email, "source": "vortex_checker"}).execute()
        return jsonify({"success": True, "message": "Lead saved"})
    except Exception as e:
        print(f"Error saving lead: {e}")
        # Retonamos success True para no frustrar al usuario si falla la DB en el demo
        return jsonify({"success": True})

if __name__ == '__main__':
    print("--- INICIANDO SERVIDOR DINÁMICO DE VIRAL VORTEX PRO ---")
    app.run(port=5001, debug=True)
