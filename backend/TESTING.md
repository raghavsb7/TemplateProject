# Testing Guide

## Prerequisites

1. **Install Dependencies**
   ```bash
   cd backend
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Set Up Database**
   ```bash
   # Using Docker (recommended)
   sudo docker compose -f ../docker-compose-db.yml up -d
   
   # Or using local PostgreSQL
   createdb app_db
   ```

3. **Configure Environment** (optional for basic testing)
   ```bash
   cp .env.example .env
   # Edit .env if you want to test OAuth integrations
   ```

## Running the Server

```bash
cd backend
source .venv/bin/activate
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000/api`

## Testing Methods

### Method 1: Automated Python Script

```bash
# Install requests if not already installed
pip install requests

# Run the test script
python test_api.py
```

### Method 2: Bash Script

```bash
# Make script executable
chmod +x test_api.sh

# Run the test script
./test_api.sh
```

### Method 3: Manual Testing with curl

#### 1. Health Check
```bash
curl http://localhost:8000/api/
```

#### 2. Create a User
```bash
curl -X POST http://localhost:8000/api/users \
  -H "Content-Type: application/json" \
  -d '{
    "email": "student@example.com",
    "name": "John Doe"
  }'
```

Save the `id` from the response for subsequent tests.

#### 3. Get User
```bash
curl http://localhost:8000/api/users/1
```

#### 4. Create Manual Task
```bash
curl -X POST "http://localhost:8000/api/tasks/manual?user_id=1" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Complete Math Homework",
    "description": "Finish chapter 5 problems",
    "task_type": "assignment",
    "due_date": "2024-12-15T23:59:59Z",
    "priority": 2
  }'
```

#### 5. Get Tasks Summary
```bash
curl "http://localhost:8000/api/tasks?user_id=1"
```

#### 6. Get Plain Language Summary
```bash
curl "http://localhost:8000/api/tasks/plain?user_id=1"
```

#### 7. Update Task Status
```bash
curl -X PUT "http://localhost:8000/api/tasks/1/status?user_id=1&status=complete"
```

#### 8. Get OAuth Login URL
```bash
curl "http://localhost:8000/api/auth/canvas/login?redirect_uri=http://localhost:5173/callback"
```

#### 9. Get Weekly Tasks
```bash
curl "http://localhost:8000/api/tasks/weekly?user_id=1"
```

### Method 4: Using Python Interactive Shell

```python
import requests

BASE_URL = "http://localhost:8000/api"

# Create user
response = requests.post(f"{BASE_URL}/users", json={
    "email": "test@example.com",
    "name": "Test User"
})
user_id = response.json()["id"]
print(f"User ID: {user_id}")

# Create task
response = requests.post(f"{BASE_URL}/tasks/manual?user_id={user_id}", json={
    "title": "Test Task",
    "task_type": "assignment",
    "due_date": "2024-12-31T23:59:59Z"
})
task_id = response.json()["id"]
print(f"Task ID: {task_id}")

# Get tasks
response = requests.get(f"{BASE_URL}/tasks?user_id={user_id}")
print(response.json())
```

### Method 5: Using Postman or Insomnia

1. Import the API collection (create one based on the endpoints)
2. Set base URL to `http://localhost:8000/api`
3. Test each endpoint individually

## Testing OAuth Integrations

OAuth testing requires actual OAuth credentials:

1. **Set up OAuth Apps:**
   - Canvas: Developer Keys in Canvas admin
   - Microsoft: Azure AD App Registration
   - Google: Google Cloud Console
   - Handshake: Contact your institution

2. **Update .env file:**
   ```env
   CANVAS_CLIENT_ID=your_client_id
   CANVAS_CLIENT_SECRET=your_client_secret
   # ... etc
   ```

3. **Test OAuth Flow:**
   ```bash
   # Get OAuth URL
   curl "http://localhost:8000/api/auth/canvas/login?redirect_uri=http://localhost:5173/callback&user_id=1"
   
   # Open the auth_url in browser
   # Complete OAuth flow
   # Handle callback with code
   ```

4. **Test Sync:**
   ```bash
   curl -X POST "http://localhost:8000/api/sync?user_id=1&source=canvas"
   ```

## Testing Database

### Check Database Connection
```bash
# Using Docker
docker exec -it my-fastapi-db psql -U postgres -d app_db

# Or locally
psql -d app_db
```

### View Tables
```sql
\dt
```

### View Users
```sql
SELECT * FROM users;
```

### View Tasks
```sql
SELECT * FROM tasks;
```

### View OAuth Tokens
```sql
SELECT id, user_id, source_type, expires_at FROM oauth_tokens;
```

## Common Issues

### 1. Database Connection Error
- Check if PostgreSQL is running
- Verify DATABASE_URL in .env
- Check database exists: `createdb app_db`

### 2. Import Errors
- Make sure you're in the backend directory
- Activate virtual environment
- Install all dependencies: `pip install -r requirements.txt`

### 3. Port Already in Use
- Change port: `uvicorn src.main:app --port 8001`
- Or kill process using port 8000

### 4. CORS Errors
- Check CORS origins in main.py
- Make sure frontend URL is in allowed origins

### 5. OAuth Errors
- Verify client IDs and secrets in .env
- Check redirect URIs match exactly
- Ensure OAuth apps are properly configured

## Expected Test Results

### Successful Health Check
```json
{
  "message": "Student Productivity Platform API",
  "status": "healthy"
}
```

### Successful User Creation
```json
{
  "id": 1,
  "email": "test@example.com",
  "name": "Test User",
  "created_at": "2024-11-08T12:00:00"
}
```

### Successful Task Summary
```json
{
  "total_tasks": 1,
  "pending_tasks": 1,
  "overdue_tasks": 0,
  "high_priority_tasks": 0,
  "tasks_by_source": {
    "manual": 1
  },
  "tasks": [...]
}
```

## Next Steps

After basic testing:
1. Test OAuth integrations with real credentials
2. Test sync functionality
3. Test background jobs (if enabled)
4. Integration testing with frontend
5. Load testing for performance

