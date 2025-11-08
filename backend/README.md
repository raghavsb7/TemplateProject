# Student Productivity Platform - Backend

Backend MVP for aggregating academic assignments, meetings, and internship opportunities from multiple platforms (Canvas, Handshake, Outlook, Google Calendar) into a unified, intelligent to-do list for students.

## Features

- ✅ OAuth 2.0 authentication for Canvas, Microsoft, Google, and Handshake
- ✅ API integrations for fetching assignments, events, and internship opportunities
- ✅ Unified task aggregation with normalization
- ✅ Task summarization and prioritization
- ✅ RESTful API endpoints
- ✅ Background job scheduler for periodic syncing
- ✅ PostgreSQL database with SQLAlchemy ORM

## Setup

### Prerequisites

- Python 3.8+
- PostgreSQL 12+
- Docker (optional, for database)

### Installation

1. **Create virtual environment:**
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

2. **Install dependencies:**
```bash
pip install -r requirements.txt
```

3. **Set up environment variables:**
```bash
cp .env.example .env
# Edit .env with your OAuth credentials
```

4. **Set up database:**
```bash
# Using Docker
sudo docker compose -f ../docker-compose-db.yml up -d

# Or using local PostgreSQL
createdb app_db
```

5. **Run database migrations:**
The database tables will be created automatically on first run.

6. **Run the server:**
```bash
uvicorn src.main:app --reload
```

The API will be available at `http://localhost:8000/api`

## API Endpoints

### User Management
- `POST /api/users` - Create a new user
- `GET /api/users/{user_id}` - Get user by ID

### OAuth Authentication
- `GET /api/auth/{source}/login` - Get OAuth authorization URL
  - Sources: `canvas`, `microsoft`, `google`, `handshake`
  - Query params: `redirect_uri`, `state` (optional)
- `POST /api/auth/{source}/callback` - Handle OAuth callback
  - Query params: `code`, `redirect_uri`, `user_id`
- `GET /api/auth/tokens` - Get all OAuth tokens for a user
  - Query params: `user_id`

### Tasks
- `GET /api/tasks` - Get summarized task list
  - Query params: `user_id`, `status` (optional)
- `GET /api/tasks/plain` - Get plain language summary
  - Query params: `user_id`
- `GET /api/tasks/weekly` - Get tasks grouped by week
  - Query params: `user_id`
- `POST /api/tasks/manual` - Create manual task
  - Query params: `user_id`
  - Body: TaskCreate schema
- `GET /api/tasks/{task_id}` - Get specific task
  - Query params: `user_id`
- `PUT /api/tasks/{task_id}/status` - Update task status
  - Query params: `user_id`, `status`
- `PUT /api/tasks/{task_id}` - Update task details
  - Query params: `user_id`
  - Body: TaskUpdate schema
- `DELETE /api/tasks/{task_id}` - Delete task
  - Query params: `user_id`

### Sync
- `POST /api/sync` - Trigger manual sync
  - Query params: `user_id`, `source` (optional)

## OAuth Setup

### Canvas
1. Go to your Canvas instance's developer keys page
2. Create a new developer key
3. Set redirect URI to: `http://your-backend-url/api/auth/canvas/callback`
4. Copy Client ID and Client Secret to `.env`

### Microsoft (Azure AD)
1. Go to Azure Portal > App Registrations
2. Create a new registration
3. Add redirect URI: `http://your-backend-url/api/auth/microsoft/callback`
4. Add API permissions: `User.Read`, `Calendars.Read`, `Mail.Read`
5. Copy Application (client) ID and Client secret to `.env`

### Google
1. Go to Google Cloud Console > APIs & Services > Credentials
2. Create OAuth 2.0 Client ID
3. Add redirect URI: `http://your-backend-url/api/auth/google/callback`
4. Enable Google Calendar API
5. Copy Client ID and Client Secret to `.env`

### Handshake
1. Contact Handshake for API access (varies by institution)
2. Set up OAuth application
3. Add redirect URI: `http://your-backend-url/api/auth/handshake/callback`
4. Copy Client ID and Client Secret to `.env`

## Database Schema

### Users
- `id` (Primary Key)
- `email` (Unique)
- `name`
- `created_at`, `updated_at`

### OAuth Tokens
- `id` (Primary Key)
- `user_id` (Foreign Key)
- `source_type` (Canvas, Outlook, Google Calendar, Handshake)
- `access_token` (Encrypted in production)
- `refresh_token`
- `expires_at`
- `created_at`, `updated_at`

### Tasks
- `id` (Primary Key)
- `user_id` (Foreign Key)
- `title`
- `description`
- `task_type` (assignment, meeting, internship, manual, email)
- `status` (pending, complete, overdue)
- `source_type`
- `source_id` (External ID from source)
- `due_date`, `start_date`
- `priority`
- `metadata` (JSON string)
- `created_at`, `updated_at`

## Background Jobs

Background syncing can be enabled by setting `ENABLE_BACKGROUND_SYNC=true` in `.env`. This will:
- Sync tasks from all connected integrations every hour
- Keep task data up-to-date automatically

## Development

### Running Tests
```bash
pytest tests/
```

### Code Structure
```
backend/
├── src/
│   ├── main.py          # FastAPI application and endpoints
│   ├── auth.py          # OAuth 2.0 authentication
│   ├── integrations.py  # API integrations
│   ├── summarizer.py    # Task summarization logic
│   └── scheduler.py     # Background job scheduler
├── models.py            # Database models and DataFetcher
├── schema.py            # Pydantic schemas and SQLAlchemy models
├── requirements.txt     # Python dependencies
└── README.md           # This file
```

## Production Deployment

1. Set `ENABLE_BACKGROUND_SYNC=true` for automatic syncing
2. Use environment variables for all configuration
3. Encrypt OAuth tokens in the database
4. Use a production-grade database (PostgreSQL)
5. Set up proper CORS origins
6. Use HTTPS for all OAuth redirects
7. Set up monitoring and logging

## License

See LICENSE file for details.

