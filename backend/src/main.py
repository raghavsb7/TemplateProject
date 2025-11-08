from fastapi import FastAPI, Depends, status, HTTPException, Query
from fastapi.requests import Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
from sqlalchemy.orm import Session
from typing import Optional, List
import os
import sys
from contextlib import asynccontextmanager

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import get_db, DataFetcher, create_db
from schema import (
    UserCreate, UserResponse, TaskCreate, TaskUpdate, TaskResponse, TaskSummary,
    TaskStatus, TaskType, SourceType, OAuthTokenResponse
)
from src.auth import OAuthHandler
from src.integrations import IntegrationManager
from src.summarizer import TaskSummarizer
from src.scheduler import scheduler

# Create database tables on startup
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    create_db()
    # Start background sync (optional - can be disabled for development)
    if os.getenv("ENABLE_BACKGROUND_SYNC", "false").lower() == "true":
        import asyncio
        asyncio.create_task(scheduler.run_periodic_sync())
    yield
    # Shutdown
    scheduler.stop()

app = FastAPI(root_path='/api', lifespan=lifespan)

# List of allowed origins
origins = [
    "http://localhost:5173",
    "http://localhost:3000",
    "http://vcm-45508.vm.duke.edu",
    os.getenv("FRONTEND_URL", "http://localhost:5173")
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Health check
@app.get("/")
async def root():
    return JSONResponse(content={"message": "Student Productivity Platform API", "status": "healthy"})


# User Management
@app.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(user: UserCreate, db: Session = Depends(get_db)):
    """Create a new user"""
    # Check if user already exists
    existing_user = DataFetcher.get_user_by_email(db, user.email)
    if existing_user:
        raise HTTPException(status_code=400, detail="User with this email already exists")
    
    new_user = DataFetcher.create_user(db, user.email, user.name)
    return new_user


@app.get("/users/{user_id}", response_model=UserResponse)
async def get_user(user_id: int, db: Session = Depends(get_db)):
    """Get user by ID"""
    user = DataFetcher.get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


# OAuth Authentication
@app.get("/auth/{source}/login")
async def oauth_login(source: str, redirect_uri: str = Query(...), state: Optional[str] = None):
    """Get OAuth authorization URL"""
    try:
        auth_url = OAuthHandler.get_auth_url(source, redirect_uri, state)
        return JSONResponse(content={"auth_url": auth_url})
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error generating auth URL: {str(e)}")


@app.post("/auth/{source}/callback")
async def oauth_callback(
    source: str,
    code: str = Query(...),
    redirect_uri: str = Query(...),
    user_id: int = Query(...),
    db: Session = Depends(get_db)
):
    """Handle OAuth callback and store tokens"""
    try:
        # Verify user exists
        user = DataFetcher.get_user(db, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Exchange code for tokens
        token_data = await OAuthHandler.exchange_code(source, code, redirect_uri)
        
        # Map source string to SourceType enum
        source_map = {
            "canvas": SourceType.CANVAS,
            "microsoft": SourceType.OUTLOOK,
            "google": SourceType.GOOGLE_CALENDAR,
            "handshake": SourceType.HANDSHAKE
        }
        
        if source not in source_map:
            raise HTTPException(status_code=400, detail=f"Unsupported source: {source}")
        
        source_type = source_map[source]
        
        # Store tokens
        token = DataFetcher.upsert_oauth_token(
            db, user_id, source_type,
            token_data["access_token"],
            token_data.get("refresh_token"),
            token_data.get("expires_at")
        )
        
        # Sync tasks immediately after authentication
        try:
            await IntegrationManager.sync_user_tasks(user_id, db, source_type)
        except Exception as e:
            # Log error but don't fail the auth
            print(f"Error syncing tasks after auth: {e}")
        
        return JSONResponse(content={
            "message": "Authentication successful",
            "token_id": token.id,
            "source": source
        })
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"OAuth callback error: {str(e)}")


@app.get("/auth/tokens", response_model=List[OAuthTokenResponse])
async def get_oauth_tokens(user_id: int = Query(...), db: Session = Depends(get_db)):
    """Get all OAuth tokens for a user"""
    user = DataFetcher.get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return user.tokens


@app.post("/auth/canvas/token")
async def add_canvas_token(
    user_id: int = Query(...),
    access_token: str = Query(...),
    canvas_base_url: str = Query(None),
    db: Session = Depends(get_db)
):
    """Add Canvas API token manually (for users without admin access)"""
    try:
        # Verify user exists
        user = DataFetcher.get_user(db, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Use provided base URL or default
        base_url = canvas_base_url or os.getenv("CANVAS_BASE_URL", "https://canvas.instructure.com")
        
        # Verify token works by making a test API call
        import httpx
        async with httpx.AsyncClient() as client:
            test_response = await client.get(
                f"{base_url}/api/v1/users/self",
                headers={"Authorization": f"Bearer {access_token}"},
                timeout=10.0
            )
            if test_response.status_code != 200:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid Canvas token. Error: {test_response.text[:200]}"
                )
        
        # Store token (API tokens don't expire, so set expires_at to None)
        token = DataFetcher.upsert_oauth_token(
            db, user_id, SourceType.CANVAS,
            access_token,
            None,  # No refresh token for API tokens
            None   # API tokens don't expire
        )
        
        # Sync tasks immediately
        try:
            await IntegrationManager.sync_user_tasks(user_id, db, SourceType.CANVAS)
        except Exception as e:
            print(f"Error syncing tasks after adding token: {e}")
        
        return JSONResponse(content={
            "message": "Canvas token added successfully",
            "token_id": token.id,
            "source": "canvas"
        })
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error adding Canvas token: {str(e)}")


# Tasks
@app.get("/tasks", response_model=TaskSummary)
async def get_tasks(
    user_id: int = Query(...),
    status_filter: Optional[TaskStatus] = Query(None, alias="status"),
    db: Session = Depends(get_db)
):
    """Get summarized task list for a user"""
    user = DataFetcher.get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    summary = TaskSummarizer.summarize_tasks(db, user_id)
    return summary


@app.get("/tasks/plain")
async def get_tasks_plain_summary(user_id: int = Query(...), db: Session = Depends(get_db)):
    """Get plain language summary of tasks"""
    user = DataFetcher.get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    summary_text = TaskSummarizer.get_plain_language_summary(db, user_id)
    return JSONResponse(content={"summary": summary_text})


@app.get("/tasks/weekly")
async def get_weekly_tasks(user_id: int = Query(...), db: Session = Depends(get_db)):
    """Get tasks grouped by week"""
    user = DataFetcher.get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    weekly_summary = TaskSummarizer.get_weekly_summary(db, user_id)
    return JSONResponse(content=weekly_summary)


@app.post("/tasks/manual", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_manual_task(
    task: TaskCreate,
    user_id: int = Query(...),
    db: Session = Depends(get_db)
):
    """Create a manual custom task"""
    user = DataFetcher.get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    new_task = DataFetcher.create_task(
        db, user_id, task.title, task.description,
        task.task_type, SourceType.MANUAL,
        task.due_date, task.start_date, task.priority
    )
    return new_task


@app.get("/tasks/{task_id}", response_model=TaskResponse)
async def get_task(task_id: int, user_id: int = Query(...), db: Session = Depends(get_db)):
    """Get a specific task"""
    task = DataFetcher.get_task(db, task_id, user_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@app.put("/tasks/{task_id}/status", response_model=TaskResponse)
async def update_task_status(
    task_id: int,
    status: TaskStatus,
    user_id: int = Query(...),
    db: Session = Depends(get_db)
):
    """Update task status"""
    task = DataFetcher.update_task_status(db, task_id, user_id, status)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@app.put("/tasks/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: int,
    task_update: TaskUpdate,
    user_id: int = Query(...),
    db: Session = Depends(get_db)
):
    """Update task details"""
    task = DataFetcher.get_task(db, task_id, user_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    if task_update.status:
        task.status = task_update.status
    if task_update.title:
        task.title = task_update.title
    if task_update.description is not None:
        task.description = task_update.description
    if task_update.priority is not None:
        task.priority = task_update.priority
    
    db.commit()
    db.refresh(task)
    return task


@app.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(task_id: int, user_id: int = Query(...), db: Session = Depends(get_db)):
    """Delete a task"""
    task = DataFetcher.get_task(db, task_id, user_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    db.delete(task)
    db.commit()
    return None


# Sync
@app.post("/sync")
async def sync_tasks(
    user_id: int = Query(...),
    source: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """Trigger manual sync of tasks from external sources"""
    user = DataFetcher.get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    source_type = None
    if source:
        source_map = {
            "canvas": SourceType.CANVAS,
            "microsoft": SourceType.OUTLOOK,
            "outlook": SourceType.OUTLOOK,
            "google": SourceType.GOOGLE_CALENDAR,
            "handshake": SourceType.HANDSHAKE
        }
        if source not in source_map:
            raise HTTPException(status_code=400, detail=f"Unsupported source: {source}")
        source_type = source_map[source]
    
    try:
        count = await IntegrationManager.sync_user_tasks(user_id, db, source_type)
        return JSONResponse(content={
            "message": "Sync completed successfully",
            "tasks_synced": count
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Sync error: {str(e)}")