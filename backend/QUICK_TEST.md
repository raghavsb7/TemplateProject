# Quick Testing Guide

## Step 1: Set Up Environment

```bash
cd /Users/aloksinha/TemplateProject/backend

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install requests  # For testing script
```

## Step 2: Set Up Database

### Option A: Using Docker (Recommended)
```bash
# From TemplateProject directory
docker compose -f docker-compose-db.yml up -d

# Wait a few seconds for database to start
sleep 5
```

### Option B: Using Local PostgreSQL
```bash
# Create database
createdb app_db

# Or use the setup script
./setup_db.sh
```

## Step 3: Configure Environment Variables

```bash
# Copy example env file
cp .env.example .env

# Edit .env (optional for basic testing)
# DATABASE_URL=postgresql://postgres:password@localhost:5432/app_db
```

## Step 4: Start the Server

```bash
# Make sure you're in the backend directory and virtual environment is activated
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

You should see:
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Application startup complete.
```

## Step 5: Test the API

### Option A: Automated Python Script

Open a new terminal window:
```bash
cd /Users/aloksinha/TemplateProject/backend
source .venv/bin/activate
python test_api.py
```

### Option B: Automated Bash Script

```bash
chmod +x test_api.sh
./test_api.sh
```

### Option C: Manual Testing with curl

#### Test 1: Health Check
```bash
curl http://localhost:8000/api/
```

Expected response:
```json
{
  "message": "Student Productivity Platform API",
  "status": "healthy"
}
```

#### Test 2: Create User
```bash
curl -X POST http://localhost:8000/api/users \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "name": "Test User"
  }'
```

Save the `id` from response (e.g., `1`)

#### Test 3: Create Task
```bash
curl -X POST "http://localhost:8000/api/tasks/manual?user_id=1" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Complete Homework",
    "description": "Math assignment due tomorrow",
    "task_type": "assignment",
    "due_date": "2024-12-15T23:59:59Z",
    "priority": 2
  }'
```

#### Test 4: Get Tasks
```bash
curl "http://localhost:8000/api/tasks?user_id=1"
```

#### Test 5: Get Plain Summary
```bash
curl "http://localhost:8000/api/tasks/plain?user_id=1"
```

#### Test 6: Update Task Status
```bash
curl -X PUT "http://localhost:8000/api/tasks/1/status?user_id=1&status=complete"
```

## Step 6: Verify Database

```bash
# Connect to database
docker exec -it my-fastapi-db psql -U postgres -d app_db

# Or if using local PostgreSQL
psql -d app_db
```

Then run SQL queries:
```sql
-- View users
SELECT * FROM users;

-- View tasks
SELECT id, title, status, task_type, due_date FROM tasks;

-- View OAuth tokens (should be empty initially)
SELECT * FROM oauth_tokens;

-- Exit
\q
```

## Testing OAuth (Optional)

OAuth testing requires actual credentials:

1. **Set up OAuth apps** in Canvas, Microsoft, Google, or Handshake
2. **Update .env** with client IDs and secrets
3. **Get OAuth URL:**
   ```bash
   curl "http://localhost:8000/api/auth/canvas/login?redirect_uri=http://localhost:5173/callback&user_id=1"
   ```
4. **Open the `auth_url` in browser** and complete OAuth flow
5. **Test sync:**
   ```bash
   curl -X POST "http://localhost:8000/api/sync?user_id=1&source=canvas"
   ```

## Troubleshooting

### Issue: "Module not found"
**Solution:** Make sure virtual environment is activated and dependencies are installed
```bash
source .venv/bin/activate
pip install -r requirements.txt
```

### Issue: "Database connection error"
**Solution:** Check if database is running
```bash
# Docker
docker ps | grep postgres

# Or check connection
psql -h localhost -U postgres -d app_db
```

### Issue: "Port 8000 already in use"
**Solution:** Use a different port
```bash
uvicorn src.main:app --reload --port 8001
```

### Issue: "Table doesn't exist"
**Solution:** Tables are created automatically on first run. Check server logs for errors.

## Quick Test Checklist

- [ ] Virtual environment created and activated
- [ ] Dependencies installed
- [ ] Database running (Docker or local)
- [ ] Server started successfully
- [ ] Health check returns 200
- [ ] Can create user
- [ ] Can create task
- [ ] Can get tasks
- [ ] Can update task status
- [ ] Database tables exist

## Next Steps

1. Test all API endpoints
2. Set up OAuth credentials for integrations
3. Test OAuth flow
4. Test sync functionality
5. Connect frontend

For more details, see [TESTING.md](TESTING.md) and [README.md](README.md)

