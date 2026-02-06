"""
Lead Finder AI - Industry Templates
====================================
Keywords y configuración PRE-DEFINIDA por industria.
El usuario solo selecciona su industria, no configura keywords.
"""

INDUSTRY_TEMPLATES = {
    # ═══════════════════════════════════════════════════════════
    # MARKETING & PUBLICIDAD
    # ═══════════════════════════════════════════════════════════
    "marketing_agency": {
        "name": "Agencia de Marketing",
        "icon": "📢",
        "description": "Encuentra negocios que necesitan ayuda con marketing, ads, SEO",
        "keywords": [
            "need help with marketing",
            "looking for marketing agency",
            "Facebook ads not working",
            "Instagram ads wasted money",
            "SEO not bringing results",
            "how to get more customers",
            "struggling with social media",
            "marketing budget wasted",
            "need more leads",
            "Google ads help",
            "need marketing strategy",
            "brand awareness help",
        ],
        "subreddits": [
            "smallbusiness", "Entrepreneur", "startups", "marketing",
            "digital_marketing", "SEO", "PPC", "socialmedia", "ecommerce"
        ],
        "platforms": ["reddit", "hackernews", "indiehackers"],
        "languages": ["en", "es"],
        "example_lead": "Local bakery owner frustrated with $2k spent on Instagram ads with no results"
    },
    
    # ═══════════════════════════════════════════════════════════
    # DESARROLLO WEB & SOFTWARE
    # ═══════════════════════════════════════════════════════════
    "web_developer": {
        "name": "Desarrollo Web / Apps",
        "icon": "💻",
        "description": "Encuentra proyectos de desarrollo, websites, aplicaciones",
        "keywords": [
            "need a developer",
            "looking for web developer",
            "website not working",
            "need help with my site",
            "looking for programmer",
            "app development help",
            "Shopify developer needed",
            "WordPress problems",
            "fix my website",
            "ecommerce site help",
            "React developer needed",
            "mobile app developer",
        ],
        "subreddits": [
            "Entrepreneur", "startups", "smallbusiness", "webdev",
            "Wordpress", "shopify", "ecommerce", "freelance"
        ],
        "platforms": ["reddit", "hackernews", "indiehackers"],
        "languages": ["en"],
        "example_lead": "Startup founder looking for React developer to build MVP"
    },
    
    # ═══════════════════════════════════════════════════════════
    # SOFTWARE B2B / SAAS
    # ═══════════════════════════════════════════════════════════
    "saas_b2b": {
        "name": "Software B2B / SaaS",
        "icon": "🚀",
        "description": "Encuentra empresas buscando herramientas y software",
        "keywords": [
            "looking for software",
            "tool recommendation",
            "best software for",
            "CRM recommendations",
            "project management tool",
            "automation software",
            "what software do you use",
            "need a better tool",
            "software to manage",
            "replacing our current",
        ],
        "subreddits": [
            "Entrepreneur", "startups", "SaaS", "smallbusiness",
            "sysadmin", "msp", "BusinessIntelligence"
        ],
        "platforms": ["reddit", "hackernews", "indiehackers"],
        "languages": ["en"],
        "example_lead": "COO looking for project management software for remote team"
    },
    
    # ═══════════════════════════════════════════════════════════
    # SALUD / DENTAL / MÉDICO
    # ═══════════════════════════════════════════════════════════
    "healthcare_dental": {
        "name": "Healthcare / Dental",
        "icon": "🦷",
        "description": "Encuentra clínicas dentales y médicas buscando software",
        "keywords": [
            "dental practice software",
            "dental clinic management",
            "patient scheduling software",
            "X-ray analysis",
            "dental AI",
            "patient no-shows",
            "medical practice management",
            "EHR recommendations",
            "telehealth software",
            "clinic automation",
        ],
        "subreddits": [
            "Dentistry", "dentalschool", "oralprofessionals",
            "medicine", "healthIT", "telehealth"
        ],
        "platforms": ["reddit", "hackernews"],
        "languages": ["en"],
        "example_lead": "Solo dentist looking for AI-powered X-ray analysis tool"
    },
    
    # ═══════════════════════════════════════════════════════════
    # COACHING & CONSULTORÍA
    # ═══════════════════════════════════════════════════════════
    "coaching_consulting": {
        "name": "Coaching / Consultoría",
        "icon": "🎯",
        "description": "Encuentra emprendedores que necesitan guía y mentoría",
        "keywords": [
            "struggling with my business",
            "need business advice",
            "feeling overwhelmed",
            "how do I grow my business",
            "stuck in my business",
            "need a mentor",
            "business coach recommendation",
            "how to scale",
            "productivity help",
            "work-life balance",
        ],
        "subreddits": [
            "Entrepreneur", "startups", "smallbusiness", "productivity",
            "getdisciplined", "consulting", "freelance"
        ],
        "platforms": ["reddit", "indiehackers"],
        "languages": ["en", "es"],
        "example_lead": "Founder feeling overwhelmed trying to scale from $10k to $50k/month"
    },
    
    # ═══════════════════════════════════════════════════════════
    # E-COMMERCE / TIENDAS ONLINE
    # ═══════════════════════════════════════════════════════════
    "ecommerce": {
        "name": "E-Commerce / Tiendas Online",
        "icon": "🛒",
        "description": "Encuentra dueños de tiendas online con problemas",
        "keywords": [
            "Shopify store slow",
            "Etsy sales down",
            "Amazon FBA help",
            "dropshipping problems",
            "ecommerce conversion rate",
            "abandoned carts",
            "product photography",
            "shipping problems",
            "inventory management",
            "online store help",
        ],
        "subreddits": [
            "ecommerce", "shopify", "Etsy", "FulfillmentByAmazon",
            "dropship", "smallbusiness", "Entrepreneur"
        ],
        "platforms": ["reddit", "indiehackers"],
        "languages": ["en"],
        "example_lead": "Etsy seller with 30% cart abandonment rate seeking solutions"
    },
    
    # ═══════════════════════════════════════════════════════════
    # DISEÑO GRÁFICO / BRANDING
    # ═══════════════════════════════════════════════════════════
    "design_branding": {
        "name": "Diseño / Branding",
        "icon": "🎨",
        "description": "Encuentra empresas que necesitan diseño, logos, branding",
        "keywords": [
            "need a logo",
            "rebranding help",
            "graphic designer needed",
            "website design help",
            "brand identity",
            "logo design",
            "UI/UX designer",
            "Figma designer",
            "packaging design",
            "visual identity help",
        ],
        "subreddits": [
            "Entrepreneur", "startups", "smallbusiness", "design_critiques",
            "graphic_design", "web_design", "logodesign"
        ],
        "platforms": ["reddit", "indiehackers"],
        "languages": ["en"],
        "example_lead": "Startup founder needing complete brand identity before launch"
    },
    
    # ═══════════════════════════════════════════════════════════
    # CONTABILIDAD / FINANZAS
    # ═══════════════════════════════════════════════════════════
    "accounting_finance": {
        "name": "Contabilidad / Finanzas",
        "icon": "📊",
        "description": "Encuentra negocios que necesitan ayuda financiera/contable",
        "keywords": [
            "need an accountant",
            "bookkeeping help",
            "tax preparation",
            "QuickBooks help",
            "financial planning",
            "CFO services",
            "business finances mess",
            "payroll problems",
            "invoicing software",
            "cash flow problems",
        ],
        "subreddits": [
            "smallbusiness", "Entrepreneur", "Accounting", "tax",
            "personalfinance", "Bookkeeping"
        ],
        "platforms": ["reddit"],
        "languages": ["en"],
        "example_lead": "Small business owner whose books are a mess before tax season"
    },
    
    # ═══════════════════════════════════════════════════════════
    # LEGAL / ABOGADOS
    # ═══════════════════════════════════════════════════════════
    "legal_services": {
        "name": "Servicios Legales",
        "icon": "⚖️",
        "description": "Encuentra empresas con necesidades legales",
        "keywords": [
            "need a lawyer",
            "legal help startup",
            "contract template",
            "terms of service help",
            "privacy policy",
            "trademark help",
            "business formation",
            "LLC vs S-Corp",
            "employment law",
            "intellectual property",
        ],
        "subreddits": [
            "Entrepreneur", "startups", "smallbusiness", "legaladvice",
            "lawfirm"
        ],
        "platforms": ["reddit", "hackernews"],
        "languages": ["en"],
        "example_lead": "SaaS founder needing terms of service and privacy policy"
    },
    
    # ═══════════════════════════════════════════════════════════
    # RECURSOS HUMANOS / RECLUTAMIENTO
    # ═══════════════════════════════════════════════════════════
    "hr_recruiting": {
        "name": "HR / Reclutamiento",
        "icon": "👥",
        "description": "Encuentra empresas con problemas de contratación",
        "keywords": [
            "how to hire",
            "finding good employees",
            "recruitment help",
            "HR software",
            "employee retention",
            "hiring remote workers",
            "job posting help",
            "interview process",
            "onboarding new employees",
            "team building",
        ],
        "subreddits": [
            "Entrepreneur", "startups", "smallbusiness", "humanresources",
            "recruiting", "jobs"
        ],
        "platforms": ["reddit", "hackernews"],
        "languages": ["en"],
        "example_lead": "Startup struggling to hire quality developers remotely"
    },
}


def get_all_industries():
    """Retorna lista de todas las industrias disponibles"""
    return [
        {
            "id": key,
            "name": data["name"],
            "icon": data["icon"],
            "description": data["description"],
            "example_lead": data.get("example_lead", "")
        }
        for key, data in INDUSTRY_TEMPLATES.items()
    ]


def get_industry_config(industry_id: str) -> dict:
    """Obtiene la configuración completa de una industria"""
    return INDUSTRY_TEMPLATES.get(industry_id, INDUSTRY_TEMPLATES["marketing_agency"])


def get_keywords_for_industry(industry_id: str) -> list:
    """Obtiene solo las keywords de una industria"""
    config = get_industry_config(industry_id)
    return config.get("keywords", [])


def get_subreddits_for_industry(industry_id: str) -> list:
    """Obtiene los subreddits de una industria"""
    config = get_industry_config(industry_id)
    return config.get("subreddits", [])


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("INDUSTRIAS DISPONIBLES EN LEAD FINDER AI")
    print("=" * 60)
    
    for industry in get_all_industries():
        print(f"\n{industry['icon']} {industry['name']}")
        print(f"   {industry['description']}")
        print(f"   Ejemplo: {industry['example_lead']}")
