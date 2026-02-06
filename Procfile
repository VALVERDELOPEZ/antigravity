# Procfile for Heroku/Render deployment
web: gunicorn app:app --bind 0.0.0.0:$PORT --workers 2 --threads 4
worker: python -m automation.scheduler
