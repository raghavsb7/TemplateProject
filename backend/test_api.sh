#!/bin/bash

# API Testing Script for Student Productivity Platform
# Make sure the server is running on http://localhost:8000

BASE_URL="http://localhost:8000/api"

echo "=== Testing Student Productivity Platform API ==="
echo ""

# Test 1: Health Check
echo "1. Testing Health Check..."
curl -s "${BASE_URL}/" | python3 -m json.tool
echo -e "\n"

# Test 2: Create a User
echo "2. Creating a test user..."
USER_RESPONSE=$(curl -s -X POST "${BASE_URL}/users" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "name": "Test User"
  }')
echo "$USER_RESPONSE" | python3 -m json.tool
USER_ID=$(echo "$USER_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['id'])")
echo -e "Created user with ID: $USER_ID\n"

# Test 3: Get User
echo "3. Getting user by ID..."
curl -s "${BASE_URL}/users/${USER_ID}" | python3 -m json.tool
echo -e "\n"

# Test 4: Create Manual Task
echo "4. Creating a manual task..."
TASK_RESPONSE=$(curl -s -X POST "${BASE_URL}/tasks/manual?user_id=${USER_ID}" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Test Assignment",
    "description": "This is a test task",
    "task_type": "assignment",
    "due_date": "2024-12-31T23:59:59Z",
    "priority": 2
  }')
echo "$TASK_RESPONSE" | python3 -m json.tool
TASK_ID=$(echo "$TASK_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['id'])")
echo -e "Created task with ID: $TASK_ID\n"

# Test 5: Get Tasks Summary
echo "5. Getting tasks summary..."
curl -s "${BASE_URL}/tasks?user_id=${USER_ID}" | python3 -m json.tool
echo -e "\n"

# Test 6: Get Plain Language Summary
echo "6. Getting plain language summary..."
curl -s "${BASE_URL}/tasks/plain?user_id=${USER_ID}" | python3 -m json.tool
echo -e "\n"

# Test 7: Update Task Status
echo "7. Updating task status to complete..."
curl -s -X PUT "${BASE_URL}/tasks/${TASK_ID}/status?user_id=${USER_ID}&status=complete" | python3 -m json.tool
echo -e "\n"

# Test 8: Get OAuth Login URL (Canvas)
echo "8. Getting Canvas OAuth login URL..."
curl -s "${BASE_URL}/auth/canvas/login?redirect_uri=http://localhost:5173/callback" | python3 -m json.tool
echo -e "\n"

# Test 9: Get OAuth Tokens (should be empty)
echo "9. Getting OAuth tokens (should be empty)..."
curl -s "${BASE_URL}/auth/tokens?user_id=${USER_ID}" | python3 -m json.tool
echo -e "\n"

echo "=== Testing Complete ==="
echo ""
echo "Note: OAuth testing requires actual OAuth credentials and user interaction."
echo "For OAuth testing, you'll need to:"
echo "1. Set up OAuth apps in Canvas, Microsoft, Google, or Handshake"
echo "2. Update .env file with client IDs and secrets"
echo "3. Use the auth URLs in a browser to complete OAuth flow"

