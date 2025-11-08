# Quick Start Guide

## Prerequisites
- Python 3.8+
- PostgreSQL 12+ (or Docker)
- OAuth credentials for the services you want to integrate

## Setup Steps

### 1. Install Dependencies
```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure Environment
```bash
cp .env.example .env
# Edit .env with your database URL and OAuth credentials
```

### 3. Start Database
```bash
# Using Docker (recommended)
sudo docker compose -f ../docker-compose-db.yml up -d

# Or use local PostgreSQL
createdb app_db
```

### 4. Run the Server
```bash
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000/api`

### 5. Test the API
```bash
# Health check
curl http://localhost:8000/api/

# Create a user
curl -X POST http://localhost:8000/api/users \
  -H "Content-Type: application/json" \
  -d '{"email": "student@example.com", "name": "John Doe"}'

# Get OAuth URL for Canvas
curl "http://localhost:8000/api/auth/canvas/login?redirect_uri=http://localhost:5173/callback"
```

## OAuth Setup (Quick Reference)

### Canvas
1. Go to Canvas > Settings > Developer Keys
2. Create new developer key
3. Set redirect URI: `http://your-backend-url/api/auth/canvas/callback`
4. Copy Client ID and Secret to `.env`

### Microsoft
1. Azure Portal > App Registrations > New Registration
2. Add redirect URI: `http://your-backend-url/api/auth/microsoft/callback`
3. Add permissions: User.Read, Calendars.Read, Mail.Read
4. Copy Client ID and Secret to `.env`

### Google
1. Google Cloud Console > APIs & Services > Credentials
2. Create OAuth 2.0 Client ID
3. Add redirect URI: `http://your-backend-url/api/auth/google/callback`
4. Enable Google Calendar API
5. Copy Client ID and Secret to `.env`

## Next Steps
1. Set up OAuth credentials for the services you want to use
2. Create a user account
3. Authenticate with each service
4. Sync tasks from connected services
5. View aggregated tasks via the API

For more details, see [README.md](README.md)

