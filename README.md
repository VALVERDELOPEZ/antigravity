# 🚀 Lead Finder AI

AI-powered lead generation SaaS that automatically scrapes, qualifies, and helps you reach out to potential customers from Reddit, Twitter, Hacker News, and more.

## 🎯 Features

- **Multi-Platform Scraping**: Automatically scrape leads from Reddit, Twitter/X, Hacker News, LinkedIn, Discord, and Indie Hackers
- **AI Lead Scoring**: GPT-4 powered scoring system that analyzes urgency, budget, and buying intent (1-10 score)
- **Personalized Email Generation**: Unique, context-aware cold emails generated for each lead
- **Automated Pipeline**: Runs every 8 hours to find new leads automatically
- **Dashboard**: Beautiful, responsive dashboard to manage leads, view analytics, and send emails
- **Stripe Integration**: Complete subscription billing system

## 📁 Project Structure

```
lead-finder-ai/
├── app.py                 # Main Flask application
├── config.py              # Configuration settings
├── models.py              # Database models
├── requirements.txt       # Python dependencies
├── .env.example           # Environment variables template
├── automation/
│   ├── __init__.py
│   ├── scraper.py         # Multi-platform web scraper
│   ├── qualifier.py       # AI lead qualification
│   ├── mailer.py          # Email generation & sending
│   ├── scheduler.py       # APScheduler automation
│   └── seeder.py          # Demo data generator
├── templates/
│   ├── base.html          # Base template
│   ├── landing.html       # Landing page
│   ├── pricing.html       # Pricing page
│   ├── auth/              # Authentication pages
│   ├── dashboard/         # Dashboard pages
│   ├── billing/           # Billing pages
│   └── errors/            # Error pages
└── static/
    ├── css/main.css       # Styles
    └── js/main.js         # JavaScript
```

## 🛠️ Installation

### 1. Clone and Setup

```bash
cd lead-finder-ai
python -m venv venv

# Windows
venv\Scripts\activate

# Mac/Linux
source venv/bin/activate

pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env with your API keys
```

Required API keys:
- **OpenAI**: For AI scoring and email generation
- **Reddit**: For Reddit scraping (create app at reddit.com/prefs/apps)
- **Twitter**: For Twitter scraping (developer.twitter.com)
- **Stripe**: For payments (dashboard.stripe.com)
- **Gmail**: For sending emails (use App Password)

### 3. Initialize Database

```bash
flask init-db
flask seed-demo  # Optional: add demo data
```

### 4. Run Locally

```bash
flask run
# or
python app.py
```

Visit: http://localhost:5000

## 🔧 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/leads` | GET | Get paginated leads |
| `/api/leads/<id>` | GET | Get single lead |
| `/api/leads/<id>/email-preview` | GET | Get email preview |
| `/api/send-email` | POST | Send email to lead |
| `/api/stats` | GET | Get dashboard stats |
| `/api/automation/status` | GET | Get automation status |
| `/webhook/stripe` | POST | Stripe webhook handler |

## 💳 Pricing Plans

| Plan | Price | Leads/mo | Emails/mo | Platforms |
|------|-------|----------|-----------|-----------|
| Free | €0 | 10 | 0 | Reddit |
| Starter | €49 | 100 | 50 | Reddit, Twitter, HN |
| Pro | €99 | 500 | 250 | All 6 platforms |
| Enterprise | Custom | Unlimited | Unlimited | All + custom |

## 🚀 Deploy to Render.com

### 1. Create Render Account
Go to [render.com](https://render.com) and sign up.

### 2. Create Web Service

1. Click **New → Web Service**
2. Connect your GitHub repo
3. Configure:
   - **Name**: lead-finder-ai
   - **Runtime**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app`

### 3. Add Environment Variables

In Render dashboard, add all variables from `.env.example`.

### 4. Add PostgreSQL Database

1. Click **New → PostgreSQL**
2. Copy the Internal Database URL
3. Add as `DATABASE_URL` environment variable

### 5. Deploy

Render will automatically deploy on push to main branch.

## 🔄 Running Automation

The automation runs automatically every 8 hours for paid users. To test manually:

```bash
# Test scraping only
python -m automation.scraper

# Test full pipeline
python -m automation.scheduler
```

## 📊 Demo Login

After running `flask seed-demo`:

- **Email**: demo@leadfinderai.com
- **Password**: demo123456

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing`)
5. Open Pull Request

## 📝 License

MIT License - feel free to use for your own projects!

## 🆘 Support

- Email: support@leadfinderai.com
- Discord: [Join our community](#)

---

Built with ❤️ using Flask, OpenAI, and Coffee ☕
