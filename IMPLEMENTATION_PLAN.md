# 🚀 LEAD FINDER AI - FEATURES CRÍTICAS PARA LANZAMIENTO (COSTE $0)

## CONTEXTO

Tenemos un SaaS funcional con scraping multi-idioma + IA. Ahora necesitamos las features MÍNIMAS para que sea vendible y cada cliente pueda usarlo para SU negocio específico.

**PRIORIDAD:** Solo features críticas, coste $0, código propio.

***

## ✅ PARTE 1: CONFIGURACIÓN POR USUARIO (CRÍTICO)

### 1.1 Keywords Personalizables

**PROBLEMA:**  
Todos los usuarios ven los mismos leads genéricos. Esto NO es útil.

**SOLUCIÓN:**  
Cada usuario configura sus propias keywords según su negocio.

**Implementación:**

**Nueva tabla: `user_keywords`**
```sql
CREATE TABLE user_keywords (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    keywords TEXT[], -- Array de keywords
    subreddits TEXT[], -- Array de subreddits
    languages TEXT[] DEFAULT ARRAY['en'], -- ['en', 'es', 'pt', 'fr']
    min_score INTEGER DEFAULT 7,
    active_platforms TEXT[] DEFAULT ARRAY['reddit', 'hn', 'indie_hackers'],
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

**UI en `/dashboard/settings`:**

Nueva sección llamada "Lead Search Configuration"

```html
<form>
  <label>Keywords (uno por línea):</label>
  <textarea rows="10" placeholder="need more clients
cold email not working
struggling to get leads
how to find customers">
  </textarea>

  <label>Subreddits (separados por comas):</label>
  <input placeholder="Entrepreneur,smallbusiness,marketing" />

  <label>Idiomas:</label>
  <checkbox> Inglés (EN)
  <checkbox> Español (ES)
  <checkbox> Portugués (PT)
  <checkbox> Francés (FR)

  <label>Score mínimo:</label>
  <slider min="1" max="10" default="7" />

  <label>Plataformas:</label>
  <checkbox> Reddit
  <checkbox> Hacker News
  <checkbox> Indie Hackers

  <button>Guardar Configuración</button>
</form>
```

**Lógica del scheduler:**

Modificar `automation/scheduler.py` para:

```python
def run_for_user(user_id):
    # 1. Obtener config del usuario
    config = get_user_keywords(user_id)
    
    # 2. Solo scrapear lo que el usuario configuró
    for language in config.languages:
        for platform in config.active_platforms:
            if platform == 'reddit':
                for subreddit in config.subreddits:
                    for keyword in config.keywords:
                        leads = scrape_reddit_json(subreddit, keyword, language)
                        # Filtrar por min_score
                        filtered = [l for l in leads if l.score >= config.min_score]
                        # Guardar con user_id
                        save_leads_for_user(filtered, user_id)
```

**CRÍTICO:**  
- Los leads en BD deben tener `user_id` para filtrar por usuario
- En `/dashboard/leads`, mostrar SOLO leads del usuario actual
- Si usuario no ha configurado keywords → mostrar mensaje: "Configura tus keywords en Settings"

***

### 1.2 Onboarding Guiado (First Login)

**Cuando usuario se registra por primera vez:**

**Nueva página: `/onboarding` (solo se muestra 1 vez)**

**Step 1: "¿Qué tipo de clientes buscas?"**
```html
<h2>¿A quién vendes?</h2>
<select>
  <option>Agencias de marketing</option>
  <option>Desarrolladores / SaaS founders</option>
  <option>Consultores / Freelancers</option>
  <option>Coaches / Mentores</option>
  <option>E-commerce / Tiendas online</option>
  <option>Otro</option>
</select>
```

**Step 2: "Keywords sugeridas"**

Basándose en su selección, pre-rellenar keywords:

```python
KEYWORD_TEMPLATES = {
    "Agencias de marketing": [
        "need more clients",
        "cold email not working",
        "struggling to get leads",
        "how to find agency clients",
        "lead generation"
    ],
    "Desarrolladores / SaaS founders": [
        "need developer",
        "looking for programmer",
        "how to build MVP",
        "struggling with development",
        "need technical co-founder"
    ],
    # ... etc
}
```

```html
<h2>Configura tus keywords</h2>
<p>Basándonos en tu selección, estas keywords te ayudarán:</p>
<textarea>{{keywords_precargadas}}</textarea>
<p><small>Puedes editarlas o añadir más</small></p>
```

**Step 3: "Selecciona idiomas"**
```html
<h2>¿En qué idiomas buscas?</h2>
<checkbox checked> Inglés (mercado más grande)
<checkbox> Español
<checkbox> Portugués
<checkbox> Francés
```

**Step 4: "¡Listo!"**
```html
<h2>¡Perfecto!</h2>
<p>Estamos buscando tus primeros leads ahora mismo.</p>
<p>Volverás a ver resultados en 30-60 minutos.</p>
<button href="/dashboard">Ir al Dashboard</button>
```

**Backend:**
- Marcar usuario con flag `onboarding_completed = true`
- Guardar su configuración en `user_keywords`
- Ejecutar scheduler inmediatamente para ese usuario

***

## ✅ PARTE 2: ENVÍO DE EMAILS DESDE PLATAFORMA

### 2.1 Botón "Send Email" en Dashboard

**En `/dashboard/leads`, añadir columna "Actions":**

```html
<td>
  <button onclick="generateEmail({{lead_id}})">Generate Email</button>
</td>
```

**Modal de preview:**

```html
<div id="emailModal">
  <h3>Email Preview</h3>
  
  <label>To:</label>
  <input value="{{lead_author_email}}" readonly />
  
  <label>Subject:</label>
  <input id="subject" value="{{generated_subject}}" />
  
  <label>Body:</label>
  <textarea id="body" rows="15">{{generated_body}}</textarea>
  
  <button onclick="sendEmail({{lead_id}})">Send Now</button>
  <button onclick="closeModal()">Cancel</button>
</div>
```

**Nueva tabla: `sent_emails`**
```sql
CREATE TABLE sent_emails (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    lead_id INTEGER REFERENCES leads(id),
    subject TEXT,
    body TEXT,
    status VARCHAR(20) DEFAULT 'sent', -- 'sent', 'opened', 'replied', 'bounced'
    sent_at TIMESTAMP DEFAULT NOW(),
    opened_at TIMESTAMP,
    replied_at TIMESTAMP
);
```

**Endpoint nuevo: `POST /api/send-email`**

```python
@app.route('/api/send-email', methods=['POST'])
def send_email():
    lead_id = request.json['lead_id']
    subject = request.json['subject']
    body = request.json['body']
    
    # 1. Obtener lead
    lead = get_lead(lead_id)
    
    # 2. Obtener config SMTP del usuario
    smtp = get_user_smtp(current_user.id)
    
    # 3. Enviar email
    send_via_smtp(
        to=lead.author_email,  # Necesitarás extraer email del autor
        subject=subject,
        body=body,
        smtp_config=smtp
    )
    
    # 4. Guardar registro
    save_sent_email(lead_id, subject, body, status='sent')
    
    # 5. Actualizar lead status
    update_lead_status(lead_id, 'contacted')
    
    return jsonify({'success': True})
```

**Email tracking (opens):**

Añadir al final del body:
```html
<img src="https://app.leadfinderai.com/track/open/{{email_id}}.png" width="1" height="1" />
```

**Endpoint: `GET /track/open/<email_id>.png`**
```python
@app.route('/track/open/<email_id>.png')
def track_open(email_id):
    # 1. Actualizar sent_emails
    mark_as_opened(email_id)
    
    # 2. Devolver imagen 1x1 transparente
    return send_file('static/pixel.png', mimetype='image/png')
```

***

### 2.2 Configuración SMTP por Usuario

**En `/dashboard/settings`, nueva sección:**

```html
<h3>Email Configuration</h3>

<form>
  <label>SMTP Server:</label>
  <input value="smtp.gmail.com" />
  
  <label>SMTP Port:</label>
  <input value="587" />
  
  <label>Email:</label>
  <input placeholder="tu-email@gmail.com" />
  
  <label>Password / App Password:</label>
  <input type="password" placeholder="xxxx-xxxx-xxxx-xxxx" />
  
  <label>From Name:</label>
  <input placeholder="Tu Nombre" />
  
  <button>Save & Test</button>
</form>

<p><small>
  Cómo obtener App Password de Gmail: 
  <a href="https://support.google.com/accounts/answer/185833">Guía aquí</a>
</small></p>
```

**Nueva tabla: `user_smtp_config`**
```sql
CREATE TABLE user_smtp_config (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) UNIQUE,
    smtp_server VARCHAR(255),
    smtp_port INTEGER,
    smtp_username VARCHAR(255),
    smtp_password_encrypted TEXT, -- Encriptada
    from_name VARCHAR(255),
    from_email VARCHAR(255),
    verified BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT NOW()
);
```

**Botón "Save & Test" hace:**
```python
# 1. Encripta password
# 2. Guarda en BD
# 3. Envía email de prueba al usuario
# 4. Si funciona → verified = true
```

***

## ✅ PARTE 3: LÍMITES POR PLAN

### 3.1 Enforcement de Límites

**Tabla de límites:**

```python
PLAN_LIMITS = {
    'free': {
        'leads_per_month': 50,
        'emails_per_month': 0,
        'languages': 1,
        'platforms': ['reddit'],
        'can_export': False
    },
    'starter': {
        'leads_per_month': 500,
        'emails_per_month': 100,
        'languages': 2,
        'platforms': ['reddit', 'hn'],
        'can_export': True
    },
    'pro': {
        'leads_per_month': 2000,
        'emails_per_month': 500,
        'languages': 4,
        'platforms': ['reddit', 'hn', 'indie_hackers'],
        'can_export': True
    }
}
```

**Nueva tabla: `user_usage`**
```sql
CREATE TABLE user_usage (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) UNIQUE,
    leads_this_month INTEGER DEFAULT 0,
    emails_this_month INTEGER DEFAULT 0,
    month_year VARCHAR(7), -- '2026-01'
    updated_at TIMESTAMP DEFAULT NOW()
);
```

**Lógica de verificación:**

```python
def can_generate_lead(user_id):
    usage = get_user_usage(user_id)
    plan = get_user_plan(user_id)
    limit = PLAN_LIMITS[plan]['leads_per_month']
    
    if usage.leads_this_month >= limit:
        return False, "Límite alcanzado. Upgrade a plan superior."
    return True, None

def can_send_email(user_id):
    usage = get_user_usage(user_id)
    plan = get_user_plan(user_id)
    limit = PLAN_LIMITS[plan]['emails_per_month']
    
    if usage.emails_this_month >= limit:
        return False, "Límite de emails alcanzado. Upgrade a Pro."
    return True, None
```

**UI cuando alcanza límite:**

```html
<div class="upgrade-banner">
  ⚠️ Has alcanzado tu límite de {{limit_type}}.
  <button href="/pricing">Upgrade a {{next_plan}}</button>
</div>
```

***

## ✅ PARTE 4: UNIFIED INBOX BÁSICO

### 4.1 Inbox de Respuestas

**Nueva sección: `/dashboard/inbox`**

**Nueva tabla: `email_replies`**
```sql
CREATE TABLE email_replies (
    id SERIAL PRIMARY KEY,
    sent_email_id INTEGER REFERENCES sent_emails(id),
    user_id INTEGER REFERENCES users(id),
    from_email VARCHAR(255),
    subject TEXT,
    body TEXT,
    replied_at TIMESTAMP DEFAULT NOW(),
    status VARCHAR(20) DEFAULT 'unread' -- 'unread', 'read', 'replied'
);
```

**UI simple:**

```html
<h2>Inbox</h2>

<table>
  <tr>
    <th>From</th>
    <th>Lead</th>
    <th>Subject</th>
    <th>Date</th>
    <th>Status</th>
  </tr>
  {% for reply in replies %}
  <tr>
    <td>{{reply.from_email}}</td>
    <td>{{reply.lead.title}}</td>
    <td>{{reply.subject}}</td>
    <td>{{reply.replied_at}}</td>
    <td>
      <span class="badge-{{reply.status}}">{{reply.status}}</span>
    </td>
  </tr>
  {% endfor %}
</table>
```

Detección de respuestas:

```python
# Script que corre cada 15 minutos: automation/check_replies.py

import imaplib
import email

def check_inbox_for_replies(user_id):
    # 1. Obtener config SMTP del usuario
    smtp_config = get_user_smtp(user_id)
    
    # 2. Conectar a IMAP
    imap = imaplib.IMAP4_SSL(smtp_config.smtp_server.replace('smtp', 'imap'))
    imap.login(smtp_config.smtp_username, smtp_config.smtp_password)
    imap.select('INBOX')
    
    # 3. Buscar emails de los últimos 7 días
    status, messages = imap.search(None, 'SINCE 7-DAYS-AGO')
    
    for msg_id in messages[0].split():
        # 4. Leer email
        _, msg_data = imap.fetch(msg_id, '(RFC822)')
        email_body = email.message_from_bytes(msg_data[0][1])
        
        from_email = email_body['From']
        subject = email_body['Subject']
        
        # 5. Verificar si es respuesta a algún email enviado
        sent_email = find_sent_email_by_recipient(from_email, user_id)
        
        if sent_email:
            # 6. Guardar respuesta
            save_reply(sent_email.id, from_email, subject, body, user_id)
            
            # 7. Actualizar sent_email status
            update_sent_email_status(sent_email.id, 'replied')
            
            # 8. Notificar usuario (opcional)
            send_notification(user_id, f"Nueva respuesta de {from_email}")
```

Añadir al scheduler principal:

```python
# Cada 15 minutos, verificar replies para todos los usuarios
for user in get_active_users():
    check_inbox_for_replies(user.id)
```

## ✅ PARTE 5: ANALYTICS BÁSICO

### 5.1 Dashboard de Métricas

Nueva sección en `/dashboard/analytics`

Métricas principales:

```xml
<div class="stats-grid">
  <div class="stat-card">
    <h3>{{total_leads}}</h3>
    <p>Total Leads (últimos 30 días)</p>
  </div>
  
  <div class="stat-card">
    <h3>{{emails_sent}}</h3>
    <p>Emails Enviados</p>
  </div>
  
  <div class="stat-card">
    <h3>{{open_rate}}%</h3>
    <p>Open Rate</p>
  </div>
  
  <div class="stat-card">
    <h3>{{reply_rate}}%</h3>
    <p>Reply Rate</p>
  </div>
</div>
```

Gráficos simples (con Chart.js - gratis):

```xml
<h3>Leads por Día (últimos 7 días)</h3>
<canvas id="leadsChart"></canvas>

<script>
const ctx = document.getElementById('leadsChart');
new Chart(ctx, {
  type: 'line',
  data: {
    labels: {{dates}},
    datasets: [{
      label: 'Leads Encontrados',
      data: {{lead_counts}},
      borderColor: 'rgb(75, 192, 192)',
    }]
  }
});
</script>
```

Endpoint: `GET /api/analytics`

```python
@app.route('/api/analytics')
def get_analytics():
    user_id = current_user.id
    
    # Últimos 30 días
    thirty_days_ago = datetime.now() - timedelta(days=30)
    
    total_leads = count_leads(user_id, since=thirty_days_ago)
    emails_sent = count_sent_emails(user_id, since=thirty_days_ago)
    
    # Open rate
    opened = count_opened_emails(user_id)
    open_rate = (opened / emails_sent * 100) if emails_sent > 0 else 0
    
    # Reply rate
    replied = count_replied_emails(user_id)
    reply_rate = (replied / emails_sent * 100) if emails_sent > 0 else 0
    
    # Leads por día (últimos 7 días)
    leads_by_day = get_leads_by_day(user_id, days=7)
    
    return jsonify({
        'total_leads': total_leads,
        'emails_sent': emails_sent,
        'open_rate': round(open_rate, 1),
        'reply_rate': round(reply_rate, 1),
        'leads_by_day': leads_by_day
    })
```

## ✅ PARTE 6: EXPORTACIÓN

### 6.1 Export Leads a CSV

En `/dashboard/leads`, añadir botón:

```xml
<button onclick="exportLeads()">Export to CSV</button>
```

Endpoint: `GET /api/export/leads?format=csv`

```python
import csv
from io import StringIO

@app.route('/api/export/leads')
def export_leads():
    user_id = current_user.id
    format = request.args.get('format', 'csv')
    
    # Verificar que usuario puede exportar
    plan = get_user_plan(user_id)
    if not PLAN_LIMITS[plan]['can_export']:
        return jsonify({'error': 'Upgrade to Starter or Pro to export'}), 403
    
    # Obtener leads del usuario
    leads = get_user_leads(user_id)
    
    # Generar CSV
    output = StringIO()
    writer = csv.writer(output)
    
    # Headers
    writer.writerow(['ID', 'Platform', 'Author', 'Title', 'Score', 'Language', 'URL', 'Created'])
    
    # Rows
    for lead in leads:
        writer.writerow([
            lead.id,
            lead.platform,
            lead.author,
            lead.title,
            lead.pain_score,
            lead.language,
            lead.url,
            lead.created_at
        ])
    
    # Devolver archivo
    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment;filename=leads.csv'}
    )
```

## ✅ PARTE 7: NOTIFICACIONES TELEGRAM

### 7.1 Notificaciones para Leads HOT

En `/dashboard/settings`, nueva sección:

```xml
<h3>Notifications</h3>

<label>Telegram Bot Token (opcional):</label>
<input placeholder="123456:ABC-DEF..." />
<small>Obtén tu bot token en <a href="https://t.me/BotFather">@BotFather</a></small>

<label>Chat ID:</label>
<input placeholder="123456789" />
<small>Envía /start a tu bot y obtén el chat_id</small>

<label>Notificar cuando:</label>
<checkbox checked> Lead con score 10/10
<checkbox> Lead con score ≥8
<checkbox> Nueva respuesta a email

<button>Guardar</button>
```

Nueva tabla: `user_notifications`

```sql
CREATE TABLE user_notifications (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) UNIQUE,
    telegram_token VARCHAR(255),
    telegram_chat_id VARCHAR(255),
    notify_on_score_10 BOOLEAN DEFAULT true,
    notify_on_score_8 BOOLEAN DEFAULT false,
    notify_on_reply BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW()
);
```

Lógica de notificación:

```python
import requests

def send_telegram_notification(user_id, message):
    config = get_user_notifications(user_id)
    
    if not config or not config.telegram_token:
        return
    
    url = f"https://api.telegram.org/bot{config.telegram_token}/sendMessage"
    
    requests.post(url, json={
        'chat_id': config.telegram_chat_id,
        'text': message,
        'parse_mode': 'HTML'
    })

# En el scheduler, después de guardar lead:
if lead.pain_score == 10 and user_config.notify_on_score_10:
    send_telegram_notification(
        user_id,
        f"🔥 <b>New HOT Lead!</b>\n\n"
        f"Score: {lead.pain_score}/10\n"
        f"Platform: {lead.platform}\n"
        f"Title: {lead.title}\n\n"
        f"<a href='https://app.leadfinderai.com/dashboard/leads/{lead.id}'>View Lead</a>"
    )
```

## ✅ PARTE 8: UI/UX MEJORAS

### 8.1 Estados Visuales de Leads

En `/dashboard/leads`, añadir columna "Status":

```xml
<td>
  <span class="badge badge-{{lead.status}}">
    {{lead.status}}
  </span>
</td>
```

Actualizar tabla leads con campo:

```sql
ALTER TABLE leads ADD COLUMN status VARCHAR(20) DEFAULT 'new';
-- Valores: 'new', 'contacted', 'replied', 'qualified', 'won', 'lost'
```

Botones de acción rápida:

```xml
<td class="actions">
  <button onclick="markAs({{lead.id}}, 'contacted')">✉️</button>
  <button onclick="markAs({{lead.id}}, 'qualified')">✓</button>
  <button onclick="markAs({{lead.id}}, 'lost')">✗</button>
</td>
```

CSS para badges:

```css
.badge-new { background: #3b82f6; }
.badge-contacted { background: #8b5cf6; }
.badge-replied { background: #10b981; }
.badge-qualified { background: #f59e0b; }
.badge-won { background: #22c55e; }
.badge-lost { background: #ef4444; }
```

### 8.2 Filtros Avanzados

En `/dashboard/leads`, añadir barra de filtros:

```xml
<div class="filters">
  <select id="filterScore">
    <option value="">Todos los scores</option>
    <option value="10">Score 10/10</option>
    <option value="9">Score ≥9</option>
    <option value="8">Score ≥8</option>
  </select>
  
  <select id="filterLanguage">
    <option value="">Todos los idiomas</option>
    <option value="en">Inglés</option>
    <option value="es">Español</option>
    <option value="pt">Portugués</option>
    <option value="fr">Francés</option>
  </select>
  
  <select id="filterPlatform">
    <option value="">Todas las plataformas</option>
    <option value="reddit">Reddit</option>
    <option value="hn">Hacker News</option>
    <option value="indie_hackers">Indie Hackers</option>
  </select>
  
  <select id="filterStatus">
    <option value="">Todos los estados</option>
    <option value="new">Nuevos</option>
    <option value="contacted">Contactados</option>
    <option value="replied">Respondidos</option>
  </select>
  
  <select id="filterTime">
    <option value="24h">Últimas 24h</option>
    <option value="7d">Últimos 7 días</option>
    <option value="30d">Últimos 30 días</option>
  </select>
  
  <button onclick="applyFilters()">Aplicar</button>
  <button onclick="resetFilters()">Limpiar</button>
</div>
```

JavaScript:

```javascript
function applyFilters() {
    const score = document.getElementById('filterScore').value;
    const language = document.getElementById('filterLanguage').value;
    const platform = document.getElementById('filterPlatform').value;
    const status = document.getElementById('filterStatus').value;
    const time = document.getElementById('filterTime').value;
    
    const params = new URLSearchParams({
        score, language, platform, status, time
    });
    
    fetch(`/api/leads?${params}`)
        .then(r => r.json())
        .then(leads => updateLeadsTable(leads));
}
```

## ✅ PARTE 9: SEGURIDAD BÁSICA

### 9.1 Unsubscribe Link

En cada email enviado, añadir al final:

```xml
<br><br>
<hr>
<p style="font-size: 11px; color: #999;">
  Don't want to receive these emails? 
  <a href="https://app.leadfinderai.com/unsubscribe/{{unsubscribe_token}}">
    Unsubscribe here
  </a>
</p>
```

Nueva tabla: `unsubscribes`

```sql
CREATE TABLE unsubscribes (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE,
    token VARCHAR(255) UNIQUE,
    unsubscribed_at TIMESTAMP DEFAULT NOW()
);
```

Endpoint: `GET /unsubscribe/<token>`

```python
@app.route('/unsubscribe/<token>')
def unsubscribe(token):
    # 1. Buscar email por token
    unsub = find_unsubscribe_by_token(token)
    
    if unsub:
        # 2. Marcar como unsubscribed
        mark_as_unsubscribed(unsub.email)
        
        return render_template('unsubscribed.html', 
            message="You've been unsubscribed successfully.")
    
    return "Invalid token", 404

# Al enviar email, verificar primero:
def can_send_to_email(email):
    return not is_unsubscribed(email)
```


# FASE 1: CRÍTICO PARA LANZAR (Esta semana)
Sin esto, el producto NO se puede vender:

✅ Keywords por usuario (tabla `user_keywords` + UI en Settings + scheduler adaptado)

✅ Onboarding guiado (página `/onboarding` con 4 steps)

✅ Envío de emails desde plataforma (botón "Send Email" + modal + endpoint `/api/send-email`)

✅ Configuración SMTP por usuario (tabla `user_smtp_config` + UI en Settings)

✅ Límites por plan (enforcement en código + banner de upgrade)

***

### FASE 2: IMPORTANTE PARA COMPETIR (Semana 2-3)

**Mejoran mucho la experiencia, pero el producto funciona sin ellas:**

6. ✅ **Unified Inbox** (página `/dashboard/inbox` + tabla `email_replies` + script `check_replies.py`)
7. ✅ **Email tracking** (opens con píxel 1×1 + endpoint `/track/open/<id>`)
8. ✅ **Analytics dashboard** (página `/dashboard/analytics` + gráficos Chart.js)
9. ✅ **Estados visuales de leads** (campo `status` + badges de colores)
10. ✅ **Filtros avanzados** (UI de filtros + JavaScript para aplicar)

**Tiempo estimado: 2-3 días de Antigravity**

***

### FASE 3: NICE TO HAVE (Semana 4+)

**Aportan valor adicional pero no son urgentes:**

11. ✅ **Exportación CSV** (endpoint `/api/export/leads`)
12. ✅ **Notificaciones Telegram** (tabla `user_notifications` + lógica de envío)
13. ✅ **Unsubscribe links** (tabla `unsubscribes` + endpoint `/unsubscribe/<token>`)

**Tiempo estimado: 1-2 días de Antigravity**

***

## 📋 CHECKLIST DE IMPLEMENTACIÓN

Para que Antigravity sepa exactamente qué hacer, en orden:

### DÍA 1-2: Keywords y Onboarding

- [ ] Crear tabla `user_keywords`
- [ ] UI en `/dashboard/settings` para configurar keywords
- [ ] Modificar `automation/scheduler.py` para leer config por usuario
- [ ] Añadir campo `user_id` a tabla `leads`
- [ ] Filtrar leads en dashboard por usuario actual
- [ ] Crear página `/onboarding` con 4 steps
- [ ] Templates de keywords predefinidos
- [ ] Marcar usuario con `onboarding_completed`

### DÍA 3: Envío de Emails

- [ ] Crear tabla `sent_emails`
- [ ] Crear tabla `user_smtp_config`
- [ ] UI en `/dashboard/settings` para configurar SMTP
- [ ] Botón "Generate Email" en `/dashboard/leads`
- [ ] Modal de preview de email
- [ ] Endpoint `POST /api/send-email`
- [ ] Lógica de envío vía SMTP
- [ ] Actualizar status del lead a "contacted"
- [ ] Botón "Test SMTP" que envía email de prueba

### DÍA 4: Límites por Plan

- [ ] Definir constante `PLAN_LIMITS` en código
- [ ] Crear tabla `user_usage`
- [ ] Script que resetea `user_usage` cada mes
- [ ] Verificación en scheduler antes de generar leads
- [ ] Verificación antes de enviar emails
- [ ] Banner/modal de "upgrade" cuando alcanza límite
- [ ] Bloquear features según plan (idiomas, plataformas, export)

### DÍA 5-6: Inbox y Tracking

- [ ] Crear tabla `email_replies`
- [ ] Script `automation/check_replies.py` que corre cada 15 min
- [ ] Conectar vía IMAP y detectar respuestas
- [ ] Página `/dashboard/inbox` con tabla de respuestas
- [ ] Añadir píxel de tracking 1×1 al body de emails
- [ ] Endpoint `GET /track/open/<email_id>.png`
- [ ] Actualizar `sent_emails.status` cuando se abre

### DÍA 7: Analytics

- [ ] Página `/dashboard/analytics`
- [ ] Calcular métricas: total leads, emails sent, open rate, reply rate
- [ ] Gráfico de leads por día (últimos 7 días) con Chart.js
- [ ] Endpoint `GET /api/analytics` que devuelve JSON

### DÍA 8: UX Mejoras

- [ ] Añadir campo `status` a tabla `leads`
- [ ] Badges visuales por status (CSS)
- [ ] Botones de acción rápida en cada lead
- [ ] Barra de filtros en `/dashboard/leads`
- [ ] JavaScript `applyFilters()` + endpoint con parámetros

### DÍA 9 (OPCIONAL): Extras

- [ ] Endpoint `/api/export/leads?format=csv`
- [ ] Verificar plan antes de permitir export
- [ ] Tabla `user_notifications` para Telegram
- [ ] UI en Settings para configurar Telegram
- [ ] Función `send_telegram_notification()`
- [ ] Tabla `unsubscribes`
- [ ] Endpoint `/unsubscribe/<token>`
- [ ] Añadir unsubscribe link a todos los emails

***

## 🎯 RESULTADO FINAL ESPERADO

Cuando todo esté implementado, el usuario podrá:

### Como Usuario Final:

1. ✅ **Registrarse** y completar onboarding guiado
2. ✅ **Configurar sus keywords específicas** según su negocio
3. ✅ **Ver solo leads relevantes** para SU nicho
4. ✅ **Ver leads en su idioma** preferido
5. ✅ **Generar email personalizado** con IA
6. ✅ **Enviar email directamente** desde la plataforma
7. ✅ **Ver si abrieron** su email (tracking)
8. ✅ **Ver respuestas** en inbox unificado
9. ✅ **Ver métricas** de performance (open rate, reply rate)
10. ✅ **Exportar leads** a CSV (planes pagos)
11. ✅ **Recibir notificaciones** en Telegram de leads HOT
12. ✅ **Filtrar y organizar** leads por score/idioma/status

### Como Propietario del SaaS (tú):

1. ✅ **Vender a múltiples clientes** con configuraciones independientes
2. ✅ **Límites automáticos** por plan sin intervención manual
3. ✅ **Upsell natural** cuando alcanzan límites
4. ✅ **Producto competitivo** vs Lemlist/Instantly
5. ✅ **Cero costes** adicionales de APIs externas
6. ✅ **Sistema 100% automatizado** que escala solo

***

## 📝 NOTAS TÉCNICAS IMPORTANTES

### Sobre SMTP

- Encriptar passwords con `cryptography.fernet` antes de guardar
- Nunca mostrar password completo en UI (solo `****`)
- Test de conexión antes de guardar config

### Sobre Scheduler

- Cada usuario debe tener su propia ejecución
- Respetar sus keywords y límites de plan
- No mostrar leads de otros usuarios

### Sobre Email Tracking

- El píxel debe ser invisible: `width="1" height="1" style="display:none"`
- Devolver siempre status 200 aunque falle el tracking

### Sobre IMAP

- Implementar rate limiting (no más de 1 conexión por minuto por usuario)
- Manejar errores de autenticación gracefully
- Si falla, no romper el sistema

### Sobre Límites

- Resetear contadores el día 1 de cada mes automáticamente
- Enviar email avisando cuando estén cerca del límite (80%, 90%, 100%)

***

## 🔄 MIGRACIONES DE BD

**Script de migración completo:**

```sql
-- 1. Keywords por usuario
CREATE TABLE user_keywords (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    keywords TEXT[],
    subreddits TEXT[],
    languages TEXT[] DEFAULT ARRAY['en'],
    min_score INTEGER DEFAULT 7,
    active_platforms TEXT[] DEFAULT ARRAY['reddit', 'hn', 'indie_hackers'],
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 2. SMTP config
CREATE TABLE user_smtp_config (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) UNIQUE,
    smtp_server VARCHAR(255),
    smtp_port INTEGER,
    smtp_username VARCHAR(255),
    smtp_password_encrypted TEXT,
    from_name VARCHAR(255),
    from_email VARCHAR(255),
    verified BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT NOW()
);

-- 3. Emails enviados
CREATE TABLE sent_emails (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    lead_id INTEGER REFERENCES leads(id),
    subject TEXT,
    body TEXT,
    status VARCHAR(20) DEFAULT 'sent',
    sent_at TIMESTAMP DEFAULT NOW(),
    opened_at TIMESTAMP,
    replied_at TIMESTAMP
);

-- 4. Respuestas recibidas
CREATE TABLE email_replies (
    id SERIAL PRIMARY KEY,
    sent_email_id INTEGER REFERENCES sent_emails(id),
    user_id INTEGER REFERENCES users(id),
    from_email VARCHAR(255),
    subject TEXT,
    body TEXT,
    replied_at TIMESTAMP DEFAULT NOW(),
    status VARCHAR(20) DEFAULT 'unread'
);

-- 5. Uso mensual
CREATE TABLE user_usage (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) UNIQUE,
    leads_this_month INTEGER DEFAULT 0,
    emails_this_month INTEGER DEFAULT 0,
    month_year VARCHAR(7),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 6. Notificaciones
CREATE TABLE user_notifications (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) UNIQUE,
    telegram_token VARCHAR(255),
    telegram_chat_id VARCHAR(255),
    notify_on_score_10 BOOLEAN DEFAULT true,
    notify_on_score_8 BOOLEAN DEFAULT false,
    notify_on_reply BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW()
);

-- 7. Unsubscribes
CREATE TABLE unsubscribes (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE,
    token VARCHAR(255) UNIQUE,
    unsubscribed_at TIMESTAMP DEFAULT NOW()
);

-- 8. Modificar tabla leads
ALTER TABLE leads ADD COLUMN user_id INTEGER REFERENCES users(id);
ALTER TABLE leads ADD COLUMN status VARCHAR(20) DEFAULT 'new';

-- 9. Modificar tabla users
ALTER TABLE users ADD COLUMN onboarding_completed BOOLEAN DEFAULT false;

-- 10. Índices para performance
CREATE INDEX idx_leads_user_id ON leads(user_id);
CREATE INDEX idx_leads_status ON leads(status);
CREATE INDEX idx_sent_emails_user_id ON sent_emails(user_id);
CREATE INDEX idx_email_replies_user_id ON email_replies(user_id);
```

***

## 📚 DOCUMENTACIÓN A ACTUALIZAR

**Archivo: `SETUP.md`**

Añadir secciones:

### Para Usuarios Nuevos:

```markdown
## Primeros Pasos

1. Regístrate en /signup
2. Completa el onboarding (4 pasos)
3. Configura tu email en Settings → Email Configuration
4. Espera 30-60 minutos para tus primeros leads
5. Envía tu primer email desde Dashboard → Leads

## Configuración de Keywords

Tus keywords determinan qué tipo de leads encontrarás.

Ejemplos:
- Si vendes servicios de marketing: "need more clients", "cold email not working"
- Si eres desarrollador: "need developer", "looking for programmer"
- Si eres consultor: "need business mentor", "how to scale business"

## Límites por Plan

- Free: 50 leads/mes, 0 emails
- Starter: 500 leads/mes, 100 emails
- Pro: 2000 leads/mes, 500 emails
```

***

## ✅ CRITERIOS DE ACEPTACIÓN

Para considerar cada feature "completa":

### Keywords por Usuario:
- [ ] Usuario puede añadir/editar keywords en Settings
- [ ] Scheduler solo scrapea con keywords del usuario
- [ ] Dashboard solo muestra leads del usuario
- [ ] Sin keywords configuradas → mensaje de ayuda

### Envío de Emails:
- [ ] Botón visible en cada lead
- [ ] Modal muestra preview editable
- [ ] Email se envía correctamente vía SMTP configurado
- [ ] Lead cambia a status "contacted"
- [ ] Se guarda registro en `sent_emails`

### Límites:
- [ ] Usuario free ve solo 50 leads/mes
- [ ] Al alcanzar límite → modal de upgrade
- [ ] No puede enviar emails si alcanzó límite
- [ ] Banner visible mostrando uso actual

### Inbox:
- [ ] Página `/dashboard/inbox` accesible
- [ ] Muestra respuestas detectadas
- [ ] Thread completo visible
- [ ] Marca como "read" al hacer click

### Analytics:
- [ ] Métricas calculadas correctamente
- [ ] Gráfico de leads por día funciona
- [ ] Actualiza en tiempo real

***

## 🚀 ORDEN DE IMPLEMENTACIÓN RECOMENDADO

**Para maximizar valor entregado por tiempo invertido:**

```
Día 1: Keywords + Leads filtrados por usuario
    ↓ (Usuario ya ve solo SUS leads relevantes)

Día 2: Onboarding guiado
    ↓ (Nueva user experience mucho mejor)

Día 3: Envío de emails + SMTP config
    ↓ (Usuario YA puede usar el producto de verdad)

Día 4: Límites por plan
    ↓ (Ahora SÍ puedes monetizar diferenciadamente)

Día 5: Tracking + Inbox
    ↓ (Usuario ve resultados de sus envíos)

Día 6: Analytics
    ↓ (Usuario ve su ROI claramente)

Día 7: UX mejoras (filtros, estados)
    ↓ (Producto se siente profesional)

Día 8-9: Extras (export, notificaciones, unsubscribe)
    ↓ (Detalles finales para competir)
```

***

## 🎯 FIN DEL DOCUMENTO

**RESUMEN EJECUTIVO PARA ANTIGRAVITY:**

Implementa estas features en el orden indicado para convertir Lead Finder AI de un MVP técnico a un producto SaaS completo y vendible.

**Prioridad máxima (Fase 1 - días 1-4):**
- Keywords personalizables
- Onboarding
- Envío de emails
- Límites por plan

Con solo esto, el producto YA se puede vender.

**Todo tiene coste $0 en APIs externas.**

**Documentación:** Actualiza `SETUP.md` y `README.md` con las nuevas features según se implementen.

**Testing:** Después de cada feature, verificar que funciona en localhost antes de pasar a la siguiente.

