#!/usr/bin/env python3
"""
API Testing Script for Student Productivity Platform
Run this after starting the server: uvicorn src.main:app --reload
"""

import requests
import json
from datetime import datetime, timedelta

BASE_URL = "http://localhost:8000/api"

def print_response(title, response):
    """Pretty print API response"""
    print(f"\n{'='*60}")
    print(f"{title}")
    print(f"{'='*60}")
    try:
        print(json.dumps(response.json(), indent=2))
    except:
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")

def test_health_check():
    """Test 1: Health Check"""
    response = requests.get(f"{BASE_URL}/")
    print_response("1. Health Check", response)
    return response.status_code == 200

def test_create_user():
    """Test 2: Create User"""
    user_data = {
        "email": f"test_{datetime.now().timestamp()}@example.com",
        "name": "Test User"
    }
    response = requests.post(f"{BASE_URL}/users", json=user_data)
    print_response("2. Create User", response)
    if response.status_code == 201:
        return response.json()["id"]
    return None

def test_get_user(user_id):
    """Test 3: Get User"""
    response = requests.get(f"{BASE_URL}/users/{user_id}")
    print_response(f"3. Get User (ID: {user_id})", response)
    return response.status_code == 200

def test_create_task(user_id):
    """Test 4: Create Manual Task"""
    task_data = {
        "title": "Test Assignment",
        "description": "This is a test task created via API",
        "task_type": "assignment",
        "due_date": (datetime.now() + timedelta(days=7)).isoformat() + "Z",
        "priority": 2
    }
    response = requests.post(
        f"{BASE_URL}/tasks/manual?user_id={user_id}",
        json=task_data
    )
    print_response("4. Create Manual Task", response)
    if response.status_code == 201:
        return response.json()["id"]
    return None

def test_get_tasks(user_id):
    """Test 5: Get Tasks Summary"""
    response = requests.get(f"{BASE_URL}/tasks?user_id={user_id}")
    print_response("5. Get Tasks Summary", response)
    return response.status_code == 200

def test_get_plain_summary(user_id):
    """Test 6: Get Plain Language Summary"""
    response = requests.get(f"{BASE_URL}/tasks/plain?user_id={user_id}")
    print_response("6. Get Plain Language Summary", response)
    return response.status_code == 200

def test_update_task_status(user_id, task_id):
    """Test 7: Update Task Status"""
    response = requests.put(
        f"{BASE_URL}/tasks/{task_id}/status?user_id={user_id}&status=complete"
    )
    print_response("7. Update Task Status", response)
    return response.status_code == 200

def test_get_oauth_url():
    """Test 8: Get OAuth Login URL"""
    response = requests.get(
        f"{BASE_URL}/auth/canvas/login",
        params={"redirect_uri": "http://localhost:5173/callback"}
    )
    print_response("8. Get Canvas OAuth Login URL", response)
    return response.status_code == 200

def test_get_tokens(user_id):
    """Test 9: Get OAuth Tokens"""
    response = requests.get(f"{BASE_URL}/auth/tokens?user_id={user_id}")
    print_response("9. Get OAuth Tokens", response)
    return response.status_code == 200

def main():
    print("="*60)
    print("Student Productivity Platform - API Testing")
    print("="*60)
    print("\nMake sure the server is running:")
    print("  uvicorn src.main:app --reload")
    print("\nPress Enter to start testing...")
    input()
    
    # Run tests
    if not test_health_check():
        print("\n❌ Health check failed! Is the server running?")
        return
    
    user_id = test_create_user()
    if not user_id:
        print("\n❌ Failed to create user!")
        return
    
    test_get_user(user_id)
    
    task_id = test_create_task(user_id)
    if task_id:
        test_get_tasks(user_id)
        test_get_plain_summary(user_id)
        test_update_task_status(user_id, task_id)
        test_get_tasks(user_id)  # Check updated status
    
    test_get_oauth_url()
    test_get_tokens(user_id)
    
    print("\n" + "="*60)
    print("Testing Complete!")
    print("="*60)
    print("\nNote: OAuth integration testing requires:")
    print("  1. OAuth credentials in .env file")
    print("  2. Actual OAuth flow in browser")
    print("  3. Valid redirect URIs configured")

if __name__ == "__main__":
    main()

