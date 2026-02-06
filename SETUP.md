# 🛠 Lead Finder AI - Guía de Configuración Completa

Esta guía te ayudará a configurar Lead Finder AI para funcionar en **modo 100% real** con **Supabase** y **scraping real** de Reddit, Hacker News e Indie Hackers.

---

## 🚀 Inicio Rápido (Local)

```powershell
# 1. Activar entorno virtual
.\venv\Scripts\activate

# 2. Instalar dependencias (incluye psycopg2 para Postgres)
pip install -r requirements.txt

# 3. Configurar .env.local con tus credenciales
# Ver secciones abajo

# 4. Inicializar base de datos (Supabase o SQLite)
flask init-db
flask seed-demo

# 5. Iniciar servidor
flask run --port 5000

# 6. Abrir en navegador
# http://localhost:5000
```

---

## 🗄️ 1. Configuración de Supabase (PostgreSQL)

### Obtener URL de conexión:

1. Ve a [supabase.com](https://supabase.com) y abre tu proyecto
2. Navega a **Settings** → **Database**
3. Copia la **Connection string** (URI format)
4. Reemplaza `[YOUR-PASSWORD]` con tu contraseña de base de datos

### Variables en `.env.local`:

```env
# Supabase PostgreSQL (formato recomendado)
DATABASE_URL=postgresql+psycopg2://postgres.xxxx:PASSWORD@aws-0-us-east-1.pooler.supabase.com:6543/postgres

# O formato alternativo que Supabase da:
# DATABASE_URL=postgres://postgres.xxxx:PASSWORD@aws-0-us-east-1.pooler.supabase.com:6543/postgres
# (el sistema lo convierte automáticamente a postgresql+psycopg2://)
```

### Inicializar tablas en Supabase:

```powershell
# Con el venv activo y DATABASE_URL configurado
flask init-db

# Esto creará las tablas:
# - users
# - leads  
# - transactions
# - automation_logs
```

### Verificar conexión:

```powershell
# El servidor mostrará la URL de conexión al iniciar
flask run --port 5000

# Deberías ver algo como:
# Using database: postgresql+psycopg2://postgres.xxx@...
```

---

## 📧 2. Configuración de Gmail SMTP (Envío de Emails Real)

Para que la app envíe correos electrónicos reales:

### Pasos:
1. **Seguridad de Google:** Ve a tu [Cuenta de Google](https://myaccount.google.com/security).
2. **2FA:** Asegúrate de que la "Verificación en dos pasos" esté **Activada**.
3. **Contraseña de Aplicación:**
   - Busca "Contraseñas de aplicaciones" en la barra de búsqueda superior.
   - Crea una nueva llamada "Lead Finder AI".
   - Google te dará una clave de **16 caracteres** (ej: `abcd efgh ijkl mnop`).

### Variables en `.env.local`:
```env
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=tu-correo@gmail.com
SMTP_PASSWORD=abcdefghijklmnop
EMAIL_FROM_NAME=Lead Finder AI
EMAIL_FROM_ADDRESS=tu-correo@gmail.com
```

### Verificar:
- Si SMTP está configurado → Los emails se envían realmente
- Si NO está configurado → Los emails se guardan en `mail_simulation.log`

---

## 💳 3. Configuración de Stripe (Modo Test)

Para activar los pagos y suscripciones:

### Pasos:
1. **API Keys:** Obtén tus claves en [Stripe Developers](https://dashboard.stripe.com/test/apikeys).
   - `STRIPE_PUBLISHABLE_KEY` (empieza por `pk_test_`)
   - `STRIPE_SECRET_KEY` (empieza por `sk_test_`)

2. **Productos:** Ve a [Productos](https://dashboard.stripe.com/test/products) y crea dos:
   - **Starter:** 49.00 EUR / Mensual
   - **Pro:** 99.00 EUR / Mensual

3. **Price IDs:** Copia el "ID de API" de cada precio (empieza por `price_`).

4. **Webhook:** Ve a [Webhooks](https://dashboard.stripe.com/test/webhooks).
   - Endpoint: `https://tu-url.render.com/webhook/stripe`
   - Eventos: `checkout.session.completed`, `customer.subscription.updated`, `customer.subscription.deleted`
   - Copia el "Secreto de firma" (`whsec_...`)

### Variables en `.env.local`:
```env
STRIPE_SECRET_KEY=sk_test_...
STRIPE_PUBLISHABLE_KEY=pk_test_...
STRIPE_PRICE_STARTER=price_...
STRIPE_PRICE_PRO=price_...
STRIPE_WEBHOOK_SECRET=whsec_...
```

---

## 🔍 4. Scraping REAL (Reddit, HN, Indie Hackers)

### Estrategia de Scraping para MVP

> **Objetivo:** Validar el mercado con coste $0 en APIs externas para conseguir los primeros 10-50 clientes.

#### ¿Por qué usamos endpoints JSON en lugar de la API oficial de Reddit?

| Aspecto | JSON Endpoints | API Oficial (PRAW) |
|---------|---------------|-------------------|
| **Coste** | $0 | $0 (free tier limitado) |
| **OAuth requerido** | ❌ No | ✅ Sí |
| **Rate limits** | ~60 req/min | 60 req/min |
| **Setup** | Ninguno | Registrar app |
| **Datos disponibles** | Posts, scores, comments | Posts, scores, comments, más |
| **Riesgo** | Bloqueo si abusamos | Bajo |

#### Fuentes implementadas:

1. **Reddit (JSON endpoints)**
   - URL: `https://www.reddit.com/r/{subreddit}/search.json?q={query}`
   - Datos: título, contenido, score, comentarios, autor
   - Rate limiting: 3-8 segundos entre requests (jitter)
   - User-Agent: rotación automática

2. **Hacker News**
   - Show HN: personas lanzando proyectos (potenciales clientes)
   - Ask HN: personas con preguntas/problemas (pain points)
   - API Firebase + BeautifulSoup

3. **Indie Hackers**
   - Feed principal con BeautifulSoup
   - Emprendedores en fase temprana

#### Protecciones implementadas:

- ✅ Rotación de User-Agent (6 navegadores diferentes)
- ✅ Jitter aleatorio (3-8 segundos entre requests)
- ✅ Máximo de requests por ciclo (configurable, default 20)
- ✅ Filtro de engagement mínimo (evita spam/bots)
- ✅ Deduplicación por external_id

### Variables de Scraping en `.env.local`:

```env
# Intervalo del scheduler (minutos)
SCRAPE_INTERVAL_MINUTES=30

# Engagement mínimo para guardar un lead (upvotes + comments)
MIN_ENGAGEMENT_SCORE=2

# Máximo requests por ciclo (rate limiting)
MAX_REQUESTS_PER_CYCLE=20
```

### Probar Scraping Manualmente:

```powershell
# Test del scraper standalone
python automation/scraper.py

# Ejecutar un ciclo del scheduler
python automation/scheduler.py --once

# Ver leads reales en la BD
sqlite3 instance/leadfinder.db "SELECT platform, source, title FROM leads WHERE source_type='real' LIMIT 10;"

# O en Supabase (desde el dashboard SQL Editor):
# SELECT platform, source, title FROM leads WHERE source_type='real' LIMIT 10;
---

## 🌐 5. Sistema Multi-Idioma (EN, ES, PT, FR)

El sistema soporta leads en **4 idiomas** desde día 1:

### Idiomas Configurados

| Idioma | Código | Bandera | Subreddits | Keywords |
|--------|--------|---------|------------|----------|
| **English** | `en` | 🇬🇧 | Entrepreneur, startups, SaaS, etc. | cold email, lead generation, etc. |
| **Español** | `es` | 🇪🇸 | Emprendedores, mexico, Colombia, etc. | email frío, necesito clientes, etc. |
| **Português** | `pt` | 🇧🇷 | Empreendedorismo, brasil, etc. | geração de leads, preciso clientes, etc. |
| **Français** | `fr` | 🇫🇷 | Entrepreneur_FR, France, etc. | génération de leads, besoin clients, etc. |

### Cómo Funciona

1. **Scraping Multi-Idioma:**
   - El scheduler scrapea todos los idiomas en paralelo
   - Cada lead se etiqueta con su idioma (`lead.language`)
   - Subreddits y keywords específicos por idioma

2. **Dashboard:**
   - Columna "Idioma" con bandera
   - Filtro por idioma en la navegación
   - Estadísticas por idioma

3. **Generación de Emails:**
   - IA detecta el idioma del lead
   - Email se genera EN EL MISMO IDIOMA del post original
   - Sistema bilingüe para todos los idiomas

4. **Scoring con IA:**
   - Análisis considera el idioma
   - Resúmenes en el idioma del lead

### Configuración de Subreddits por Idioma

```python
# automation/scraper.py

SUBREDDITS_BY_LANGUAGE = {
    "en": ["Entrepreneur", "startups", "smallbusiness", "GrowthHacking", "SaaS"],
    "es": ["Emprendedores", "mexico", "Colombia", "argentina", "es"],
    "pt": ["Empreendedorismo", "brasil", "investimentos", "brdev"],
    "fr": ["Entrepreneur_FR", "France", "besoindeparler", "vosfinances"]
}

KEYWORDS_BY_LANGUAGE = {
    "en": ["cold email", "lead generation", "B2B growth", "need clients"],
    "es": ["email frío", "necesito clientes", "busco clientes", "crecimiento B2B"],
    "pt": ["geração de leads", "preciso clientes", "email frio"],
    "fr": ["génération de leads", "besoin clients", "email froid"]
}
```

### Añadir un Nuevo Idioma

Para agregar un nuevo idioma (ej: italiano):

1. **Modificar `automation/scraper.py`:**
   ```python
   SUBREDDITS_BY_LANGUAGE["it"] = ["italy", "startup_italia", "imprenditorialita"]
   KEYWORDS_BY_LANGUAGE["it"] = ["generazione lead", "bisogno clienti"]
   LANGUAGE_INFO["it"] = {"name": "Italiano", "flag": "🇮🇹", "display": "IT"}
   ```

2. **Actualizar la migración de BD:**
   ```sql
   -- El campo language ya soporta cualquier código ISO de 2-5 caracteres
   -- No se necesita migración adicional
   ```

3. **Actualizar el dashboard (`templates/dashboard/leads.html`):**
   ```html
   <option value="it">🇮🇹 Italiano</option>
   
   {% elif lead.language == 'it' %}
   🇮🇹 IT
   ```

4. **Actualizar `automation/ai_generator.py`:**
   ```python
   language_config['it'] = {
       'instruction': "Scrivi l'email IN ITALIANO.",
       'system': "Sei un esperto nella scrittura di email a freddo."
   }
   ```

### Verificar Multi-Idioma

```powershell
# Ejecutar scraping multi-idioma
python automation/scheduler.py --once

# Ver leads por idioma en Supabase:
# SELECT language, COUNT(*) FROM leads GROUP BY language;

# Ver en el dashboard: /dashboard/leads
# Usar el filtro de idioma para ver leads específicos
```

---

## 🤖 6. Scheduler de Automatización

El scheduler busca leads automáticamente cada X minutos.

### Ejecutar en Local:

```powershell
# En una terminal separada (con venv activo)
python automation/scheduler.py

# O ejecutar solo un ciclo (para testing):
python automation/scheduler.py --once
```

### Variables de Control:

```env
# Para MVP (actualizaciones frecuentes)
SCRAPE_INTERVAL_MINUTES=30

# Para producción (menos agresivo)
SCRAPE_INTERVAL_HOURS=8
```

### En Render (Background Worker):

1. Crea un nuevo **Background Worker** en Render
2. Configuración:
   - **Build Command:** `pip install -r requirements-prod.txt`
   - **Start Command:** `python automation/scheduler.py`
3. Añade las mismas variables de entorno que el Web Service

---

## 🏭 7. Modo Producción (100% Real) - CHECKLIST

### Requisitos Mínimos:

| Componente | Variable | Obligatorio |
|------------|----------|-------------|
| Supabase (DB) | `DATABASE_URL` | ✅ Sí |
| OpenAI (Scoring) | `OPENAI_API_KEY` | ✅ Sí |
| Gmail (Emails) | `SMTP_*` variables | ⚡ Recomendado |
| Stripe (Pagos) | `STRIPE_*` variables | ⚡ Recomendado |

### Checklist de Producción:

- [ ] `.env.local` tiene `DATABASE_URL` de Supabase (PostgreSQL)
- [ ] Ejecuté `flask init-db` y las tablas se crearon en Supabase
- [ ] `.env.local` tiene `OPENAI_API_KEY` real
- [ ] `.env.local` tiene configuración SMTP completa
- [ ] Probé el scraper: `python automation/scraper.py` funciona
- [ ] Los leads en el dashboard muestran la fuente real:
  - `Reddit (Entrepreneur)`, `Reddit (SaaS)`, etc.
  - `HN (Show HN)`, `HN (Ask HN)`
  - `IndieH (real)`
- [ ] El scheduler está corriendo: `python automation/scheduler.py`
- [ ] El scheduler genera leads reales cada 30 minutos
- [ ] (Opcional) Stripe está configurado y los pagos funcionan en modo test

### Cómo Saber si Está en Modo Real:

1. **En el Dashboard de Leads:** La columna "Fuente" muestra:
   - 🟢 **Reddit (subreddit)** = Scraped real de Reddit
   - 🟢 **HN (Show HN)** = Scraped real de Hacker News
   - 🟢 **IndieH (real)** = Scraped real de Indie Hackers
   - 🟣 **AI** = Generado por IA (fallback)
   - ⚪ **Demo** = Datos de prueba

2. **En logs del scheduler:**
   ```
   LEAD FINDER AI - REAL SCRAPING SCHEDULER
   Mode: PRODUCTION (Real Scraping)
   Sources: Reddit JSON, Hacker News, Indie Hackers
   ```

---

## ✅ 8. Checklist Final de Validación

### Autenticación:
- [ ] Puedo registrarme en `/signup`
- [ ] Puedo loguearme con `demo@leadfinderai.com` / `demo123456`
- [ ] Veo el dashboard con estadísticas

### Base de Datos:
- [ ] La app usa PostgreSQL (Supabase) en producción
- [ ] Las tablas existen: `users`, `leads`, `automation_logs`
- [ ] Puedo ver datos en el dashboard de Supabase

### Leads:
- [ ] Ejecuto `python automation/scheduler.py --once` sin errores
- [ ] Veo los nuevos leads en `/dashboard/leads`
- [ ] Los leads REALES muestran la fuente específica (Reddit/HN/IndieH)
- [ ] El campo `source_type` es `real` para leads scrapeados

### Emails:
- [ ] Click en el icono de sobre para generar email
- [ ] El email se genera con IA (personalizado al lead)
- [ ] Con SMTP configurado, el email se envía realmente
- [ ] Sin SMTP, el email aparece en `mail_simulation.log`

### Pagos (Opcional):
- [ ] Click "Upgrade" abre Stripe Checkout
- [ ] Pago con tarjeta test `4242 4242 4242 4242` → Success
- [ ] El plan se actualiza en Settings

### Scheduler:
- [ ] `python automation/scheduler.py` inicia sin errores
- [ ] Muestra "REAL SCRAPING SCHEDULER"
- [ ] Genera leads cada 30 minutos (configurable)

---

## 🔧 Comandos Útiles

```powershell
# Activar entorno
.\venv\Scripts\activate

# Iniciar servidor
flask run --port 5000

# Ejecutar un ciclo de scraping (testing)
python automation/scheduler.py --once

# Iniciar scheduler continuo
python automation/scheduler.py

# Test standalone del scraper
python automation/scraper.py

# Inicializar BD en Supabase
flask init-db

# Crear usuario demo
flask seed-demo

# Ver variables de entorno cargadas
python -c "from dotenv import load_dotenv; load_dotenv('.env.local'); import os; print(os.getenv('DATABASE_URL')[:50])"
```

---

## 📁 Archivos de Configuración

| Archivo | Propósito |
|---------|-----------|
| `.env.local` | Variables de entorno (TUS claves) |
| `.env.example` | Plantilla con todas las variables |
| `config.py` | Configuración de la app (lee de .env) |
| `render.yaml` | Blueprint para deploy en Render |
| `requirements.txt` | Dependencias de desarrollo |
| `requirements-prod.txt` | Dependencias de producción |

---

## 🗄️ Esquema de Base de Datos

### Tabla `users`
```sql
id, email, password_hash, name, plan, stripe_customer_id, 
keywords, platforms, leads_found_count, emails_sent_count, ...
```

### Tabla `leads`
```sql
id, user_id, username, platform, title, content, post_url,
external_id,  -- ID del post en la plataforma origen
source,       -- "r/Entrepreneur", "Show HN", etc.
source_type,  -- 'real', 'ai_generated', 'demo'
score, urgency, status, email_sent, ...
```

### Tabla `automation_logs`
```sql
id, event_type, platform, status, leads_found, 
message, error_message, created_at, ...
```

---

## 🚨 Migración de SQLite a Supabase

Si ya tienes datos en SQLite y quieres migrarlos a Supabase:

```python
# Script de migración (ejecutar una vez)
# migrate_to_supabase.py

import sqlite3
import os
from dotenv import load_dotenv
load_dotenv('.env.local')

# 1. Exportar de SQLite
conn = sqlite3.connect('instance/leadfinder.db')
# ... exportar a CSV o usar pg_dump

# 2. Importar a Supabase
# Usar el SQL Editor de Supabase o herramientas como DBeaver
```

Para proyectos nuevos, simplemente configura `DATABASE_URL` de Supabase y ejecuta `flask init-db`.

---

## 📊 Métricas de Rendimiento Esperadas

| Métrica | Valor Esperado |
|---------|---------------|
| Leads por ciclo | 5-20 |
| Tiempo por ciclo | 2-5 minutos |
| Requests por ciclo | 10-20 |
| Leads duplicados | 0 (deduplicación activa) |
| Tasa de leads "hot" (8+) | 20-30% |

---

*Última actualización: Enero 2026*
