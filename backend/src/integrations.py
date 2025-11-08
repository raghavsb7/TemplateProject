"""
API Integration connectors for Canvas, Microsoft Graph, Google Calendar, and Handshake
"""
import os
import httpx
import json
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta, timezone
from dateutil import parser
import sys
import os
# Add parent directory to path for imports
if os.path.dirname(os.path.dirname(os.path.abspath(__file__))) not in sys.path:
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from schema import SourceType, TaskType, TaskStatus, Task
from models import get_db

CANVAS_BASE_URL = os.getenv("CANVAS_BASE_URL", "https://canvas.instructure.com")


class BaseIntegration:
    """Base class for API integrations"""
    
    def __init__(self, access_token: str):
        self.access_token = access_token
    
    async def fetch_tasks(self, user_id: int, db) -> List[Dict[str, Any]]:
        """Fetch and normalize tasks from the API"""
        raise NotImplementedError
    
    def normalize_task(self, raw_data: Dict[str, Any], source_type: SourceType) -> Dict[str, Any]:
        """Normalize external API data to internal task format"""
        raise NotImplementedError


class CanvasIntegration(BaseIntegration):
    """Canvas LMS API Integration"""
    
    async def fetch_tasks(self, user_id: int, db) -> List[Dict[str, Any]]:
        """Fetch assignments from Canvas"""
        tasks = []
        async with httpx.AsyncClient() as client:
            # Get user's courses
            courses_response = await client.get(
                f"{CANVAS_BASE_URL}/api/v1/courses",
                headers={"Authorization": f"Bearer {self.access_token}"},
                params={"enrollment_type": "student", "enrollment_state": "active"}
            )
            if courses_response.status_code != 200:
                return tasks
            
            courses = courses_response.json()
            
            # Get assignments for each course
            for course in courses:
                assignments_response = await client.get(
                    f"{CANVAS_BASE_URL}/api/v1/courses/{course['id']}/assignments",
                    headers={"Authorization": f"Bearer {self.access_token}"},
                    params={"bucket": "upcoming"}
                )
                if assignments_response.status_code == 200:
                    assignments = assignments_response.json()
                    for assignment in assignments:
                        if assignment.get("due_at"):
                            task = self.normalize_task({
                                **assignment,
                                "course_name": course.get("name", "Unknown Course"),
                                "course_id": course["id"]
                            }, SourceType.CANVAS)
                            task["user_id"] = user_id
                            tasks.append(task)
        
        return tasks
    
    def normalize_task(self, raw_data: Dict[str, Any], source_type: SourceType) -> Dict[str, Any]:
        """Normalize Canvas assignment to task format"""
        due_date = None
        if raw_data.get("due_at"):
            due_date = parser.parse(raw_data["due_at"])
        
        # Calculate priority: higher priority for tasks due soon
        priority = 0
        if due_date:
            try:
                # Ensure due_date is timezone-aware
                if due_date.tzinfo is None:
                    due_date = due_date.replace(tzinfo=timezone.utc)
                hours_until_due = (due_date - datetime.now(timezone.utc)).total_seconds() / 3600
                if hours_until_due < 24:
                    priority = 3
                elif hours_until_due < 48:
                    priority = 2
                elif hours_until_due < 168:  # 1 week
                    priority = 1
            except Exception:
                priority = 0
        
        metadata = {
            "course_name": raw_data.get("course_name"),
            "course_id": raw_data.get("course_id"),
            "points_possible": raw_data.get("points_possible"),
            "submission_types": raw_data.get("submission_types", [])
        }
        
        return {
            "title": raw_data.get("name", "Untitled Assignment"),
            "description": raw_data.get("description", ""),
            "task_type": TaskType.ASSIGNMENT,
            "source_type": source_type,
            "source_id": str(raw_data.get("id")),
            "due_date": due_date,
            "priority": priority,
            "task_metadata": json.dumps(metadata)
        }


class MicrosoftGraphIntegration(BaseIntegration):
    """Microsoft Graph API Integration for Outlook Calendar and Mail"""
    
    async def fetch_tasks(self, user_id: int, db) -> List[Dict[str, Any]]:
        """Fetch events and emails from Microsoft Graph"""
        tasks = []
        async with httpx.AsyncClient() as client:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            base_url = "https://graph.microsoft.com/v1.0"
            
            # Fetch calendar events
            now = datetime.now(timezone.utc)
            end_date = now + timedelta(days=30)
            events_response = await client.get(
                f"{base_url}/me/calendar/events",
                headers=headers,
                params={
                    "startDateTime": now.isoformat(),
                    "endDateTime": end_date.isoformat(),
                    "$filter": "isAllDay eq false",
                    "$orderby": "start/dateTime"
                }
            )
            if events_response.status_code == 200:
                events = events_response.json().get("value", [])
                for event in events:
                    task = self.normalize_calendar_event(event, SourceType.OUTLOOK)
                    task["user_id"] = user_id
                    tasks.append(task)
            
            # Fetch important emails (potential internship opportunities)
            # Look for emails with keywords or from certain senders
            mail_response = await client.get(
                f"{base_url}/me/messages",
                headers=headers,
                params={
                    "$filter": "isRead eq false and importance eq 'high'",
                    "$top": 50,
                    "$orderby": "receivedDateTime desc"
                }
            )
            if mail_response.status_code == 200:
                messages = mail_response.json().get("value", [])
                for message in messages:
                    # Check if email is internship-related
                    subject = message.get("subject", "").lower()
                    body = message.get("body", {}).get("content", "").lower()
                    keywords = ["internship", "interview", "application", "job", "opportunity", "position"]
                    if any(keyword in subject or keyword in body for keyword in keywords):
                        task = self.normalize_email(message, SourceType.OUTLOOK)
                        task["user_id"] = user_id
                        tasks.append(task)
        
        return tasks
    
    def normalize_calendar_event(self, raw_data: Dict[str, Any], source_type: SourceType) -> Dict[str, Any]:
        """Normalize Outlook calendar event to task format"""
        start_date = None
        due_date = None
        if raw_data.get("start"):
            start_date = parser.parse(raw_data["start"].get("dateTime"))
        if raw_data.get("end"):
            due_date = parser.parse(raw_data["end"].get("dateTime"))
        
        priority = 0
        if start_date:
            try:
                if start_date.tzinfo is None:
                    start_date = start_date.replace(tzinfo=timezone.utc)
                hours_until = (start_date - datetime.now(timezone.utc)).total_seconds() / 3600
                priority = 1 if hours_until < 24 else 0
            except Exception:
                priority = 0
        
        metadata = {
            "location": raw_data.get("location", {}).get("displayName"),
            "organizer": raw_data.get("organizer", {}).get("emailAddress", {}).get("name"),
            "attendees_count": len(raw_data.get("attendees", []))
        }
        
        return {
            "title": raw_data.get("subject", "Untitled Meeting"),
            "description": raw_data.get("bodyPreview", ""),
            "task_type": TaskType.MEETING,
            "source_type": source_type,
            "source_id": raw_data.get("id"),
            "due_date": due_date,
            "start_date": start_date,
            "priority": priority,
            "task_metadata": json.dumps(metadata)
        }
    
    def normalize_email(self, raw_data: Dict[str, Any], source_type: SourceType) -> Dict[str, Any]:
        """Normalize Outlook email to task format"""
        received_date = None
        if raw_data.get("receivedDateTime"):
            received_date = parser.parse(raw_data["receivedDateTime"])
        
        metadata = {
            "sender": raw_data.get("from", {}).get("emailAddress", {}).get("address"),
            "sender_name": raw_data.get("from", {}).get("emailAddress", {}).get("name"),
            "has_attachments": raw_data.get("hasAttachments", False)
        }
        
        return {
            "title": raw_data.get("subject", "Untitled Email"),
            "description": raw_data.get("bodyPreview", ""),
            "task_type": TaskType.EMAIL,
            "source_type": source_type,
            "source_id": raw_data.get("id"),
            "due_date": received_date,
            "priority": 2,  # Important emails get higher priority
            "task_metadata": json.dumps(metadata)
        }


class GoogleCalendarIntegration(BaseIntegration):
    """Google Calendar API Integration"""
    
    async def fetch_tasks(self, user_id: int, db) -> List[Dict[str, Any]]:
        """Fetch events from Google Calendar"""
        tasks = []
        async with httpx.AsyncClient() as client:
            now = datetime.now(timezone.utc)
            time_min = now.isoformat()
            time_max = (now + timedelta(days=30)).isoformat()
            
            events_response = await client.get(
                "https://www.googleapis.com/calendar/v3/calendars/primary/events",
                headers={"Authorization": f"Bearer {self.access_token}"},
                params={
                    "timeMin": time_min,
                    "timeMax": time_max,
                    "singleEvents": "true",
                    "orderBy": "startTime"
                }
            )
            if events_response.status_code == 200:
                events = events_response.json().get("items", [])
                for event in events:
                    task = self.normalize_task(event, SourceType.GOOGLE_CALENDAR)
                    task["user_id"] = user_id
                    tasks.append(task)
        
        return tasks
    
    def normalize_task(self, raw_data: Dict[str, Any], source_type: SourceType) -> Dict[str, Any]:
        """Normalize Google Calendar event to task format"""
        start_date = None
        due_date = None
        
        if raw_data.get("start"):
            start_str = raw_data["start"].get("dateTime") or raw_data["start"].get("date")
            if start_str:
                start_date = parser.parse(start_str)
        
        if raw_data.get("end"):
            end_str = raw_data["end"].get("dateTime") or raw_data["end"].get("date")
            if end_str:
                due_date = parser.parse(end_str)
        
        priority = 0
        if start_date:
            try:
                if start_date.tzinfo is None:
                    start_date = start_date.replace(tzinfo=timezone.utc)
                hours_until = (start_date - datetime.now(timezone.utc)).total_seconds() / 3600
                priority = 1 if hours_until < 24 else 0
            except Exception:
                priority = 0
        
        metadata = {
            "location": raw_data.get("location"),
            "organizer": raw_data.get("organizer", {}).get("email"),
            "hangout_link": raw_data.get("hangoutLink")
        }
        
        return {
            "title": raw_data.get("summary", "Untitled Event"),
            "description": raw_data.get("description", ""),
            "task_type": TaskType.MEETING,
            "source_type": source_type,
            "source_id": raw_data.get("id"),
            "due_date": due_date,
            "start_date": start_date,
            "priority": priority,
            "task_metadata": json.dumps(metadata)
        }


class HandshakeIntegration(BaseIntegration):
    """Handshake API Integration (placeholder)"""
    
    async def fetch_tasks(self, user_id: int, db) -> List[Dict[str, Any]]:
        """Fetch internship opportunities from Handshake"""
        tasks = []
        # Handshake API implementation depends on institution access
        # This is a placeholder that can be extended based on available API
        async with httpx.AsyncClient() as client:
            try:
                # Example endpoint - adjust based on actual Handshake API
                response = await client.get(
                    "https://api.joinhandshake.com/v1/jobs",
                    headers={"Authorization": f"Bearer {self.access_token}"},
                    params={"per_page": 50}
                )
                if response.status_code == 200:
                    jobs = response.json().get("data", [])
                    for job in jobs:
                        task = self.normalize_task(job, SourceType.HANDSHAKE)
                        task["user_id"] = user_id
                        tasks.append(task)
            except Exception as e:
                # If API is not available, return empty list
                print(f"Handshake API error: {e}")
        
        return tasks
    
    def normalize_task(self, raw_data: Dict[str, Any], source_type: SourceType) -> Dict[str, Any]:
        """Normalize Handshake job posting to task format"""
        due_date = None
        priority = 1
        
        if raw_data.get("application_deadline"):
            due_date = parser.parse(raw_data["application_deadline"])
            # Calculate priority based on deadline
            try:
                if due_date.tzinfo is None:
                    due_date = due_date.replace(tzinfo=timezone.utc)
                days_until = (due_date - datetime.now(timezone.utc)).total_seconds() / 86400
                if days_until < 7:
                    priority = 2
            except Exception:
                priority = 1
        
        metadata = {
            "employer": raw_data.get("employer", {}).get("name") if isinstance(raw_data.get("employer"), dict) else None,
            "job_type": raw_data.get("job_type"),
            "location": raw_data.get("location", {}).get("name") if isinstance(raw_data.get("location"), dict) else None
        }
        
        return {
            "title": raw_data.get("title", "Untitled Job Posting"),
            "description": raw_data.get("description", ""),
            "task_type": TaskType.INTERNSHIP,
            "source_type": source_type,
            "source_id": str(raw_data.get("id")),
            "due_date": due_date,
            "priority": priority,
            "task_metadata": json.dumps(metadata)
        }


class IntegrationManager:
    """Manages all integrations and data aggregation"""
    
    @staticmethod
    async def sync_user_tasks(user_id: int, db, source_type: Optional[SourceType] = None):
        """Sync tasks from all connected integrations for a user"""
        from models import DataFetcher
        
        # Get user's OAuth tokens
        sources = [SourceType.CANVAS, SourceType.OUTLOOK, SourceType.GOOGLE_CALENDAR, SourceType.HANDSHAKE]
        if source_type:
            sources = [source_type]
        
        all_tasks = []
        for source in sources:
            token = DataFetcher.get_oauth_token(db, user_id, source)
            if not token:
                continue
            
            # Check if token is expired and refresh if needed
            if token.expires_at and token.expires_at < datetime.now(timezone.utc):
                # Refresh token logic would go here
                # For now, skip expired tokens
                continue
            
            # Fetch tasks based on source
            integration = None
            if source == SourceType.CANVAS:
                integration = CanvasIntegration(token.access_token)
            elif source == SourceType.OUTLOOK:
                integration = MicrosoftGraphIntegration(token.access_token)
            elif source == SourceType.GOOGLE_CALENDAR:
                integration = GoogleCalendarIntegration(token.access_token)
            elif source == SourceType.HANDSHAKE:
                integration = HandshakeIntegration(token.access_token)
            
            if integration:
                try:
                    tasks = await integration.fetch_tasks(user_id, db)
                    all_tasks.extend(tasks)
                except Exception as e:
                    print(f"Error fetching tasks from {source}: {e}")
        
        # Upsert tasks to database (avoid duplicates)
        from models import DataFetcher
        
        for task_data in all_tasks:
            # Check if task already exists
            existing_task = db.query(Task).filter(
                Task.user_id == user_id,
                Task.source_id == task_data.get("source_id"),
                Task.source_type == task_data.get("source_type")
            ).first()
            
            if existing_task:
                # Update existing task
                for key, value in task_data.items():
                    if key != "user_id" and hasattr(existing_task, key):
                        setattr(existing_task, key, value)
            else:
                # Create new task
                DataFetcher.create_task(
                    db,
                    user_id=task_data.get("user_id"),
                    title=task_data.get("title"),
                    description=task_data.get("description"),
                    task_type=task_data.get("task_type"),
                    source_type=task_data.get("source_type"),
                    due_date=task_data.get("due_date"),
                    start_date=task_data.get("start_date"),
                    priority=task_data.get("priority", 0),
                    source_id=task_data.get("source_id"),
                    task_metadata=task_data.get("task_metadata")
                )
        
        db.commit()
        return len(all_tasks)

