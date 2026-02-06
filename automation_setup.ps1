# Ghost License Reaper - Automation Deployer
# This script prepares the marketing engine for 24/7 operation.

echo "🤖 Initializing Marketing Automation Machine..."

# 1. Create Virtual Environment if not exists
if (!(Test-Path "venv")) {
    echo "📦 Creating Python Virtual Environment..."
    python -m venv venv
}

# 2. Activate and Install Dependencies
echo "🛠️ Installing dependencies..."
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt

# 3. Verify .env.local
if (!(Test-Path ".env.local")) {
    echo "⚠️ .env.local not found. Creating from example..."
    Copy-Item .env.example .env.local
    echo "‼️ ACTION REQUIRED: Please fill in your API keys in .env.local"
}

# 4. Initialize Database
echo "🗄️ Initializing database schema..."
flask init-db

# 5. Instructions for Background Running
echo "----------------------------------------------------"
echo "✅ Setup Complete!"
echo "----------------------------------------------------"
echo "🚀 To start the MARKETING MACHINE 24/7, run:"
echo "   .\venv\Scripts\python.exe automation\scheduler.py"
echo ""
echo "💡 To run as a permanent background service on Windows:"
echo "   Use Task Scheduler to run this command every time the system starts."
echo "----------------------------------------------------"
