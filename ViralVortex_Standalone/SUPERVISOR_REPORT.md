# Informe del Supervisor: Viral Vortex

**Estado General: PLANIFICACIÓN CRÍTICA**
El diseño es ambicioso y se basa en datos sólidos, pero presenta riesgos técnicos elevados en la ejecución de la "mimetización humana".

## 2. Puntos Flacos Detectados
- **Riesgo de Detección (Shadowban)**: Las capas de "Humanizer" actuales en el mercado son insuficientes. Si fallamos aquí, las cuentas morirán en <24h.
- **Acoplamiento n8n**: El sistema depende totalmente de n8n para el envío. Se necesita un mecanismo de "Circuit Breaker" local.
- **Escalabilidad de Personas**: Gestionar >10 personas con historias consistentes sin que la IA se contradiga es un reto de "Memoria de Largo Plazo" (RAG).

## 3. Errores Potenciales
- Falta de validación de proxies residenciales en el PRD.
- Ausencia de un sistema de "Enfriamiento" (Cooldown) natural entre publicaciones.

## 4. Órdenes de Mejora (Orders)
1. **[ORDEN]** Implementa el "Humanizer" usando una técnica de *Double-Prompting*: uno para generar y otro para "ensuciar" el texto con errores humanos realistas.
2. **[ORDEN]** Integra un sistema de **Proxy Rotation** por persona. Nunca compartas IP entre dos hilos de conversación.
3. **[ORDEN]** Crea un **Sentinel** que verifique si el post sigue vivo (no shadowbanned) 15 minutos después de publicar.
4. **[ORDEN]** Usa **Vector Search** (Supabase Vector) para que cada persona tenga acceso a sus posts anteriores y "recuerde" su estilo.

## 5. Plan de Ejecución Inmediata
1. Setup de la base de datos de Personas en Supabase.
2. Desarrollo del Prototipo del "Sentinel" de sentimiento.
3. Prueba de estrés de la capa de Humanización.
