"""
Task Summarization and Prioritization Logic
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import List, Dict, Any
from datetime import datetime, timedelta, timezone
from schema import Task, TaskStatus, TaskType, SourceType, TaskSummary, TaskResponse
from models import DataFetcher
from sqlalchemy.orm import Session


class TaskSummarizer:
    """Handles task summarization and prioritization"""
    
    @staticmethod
    def summarize_tasks(db: Session, user_id: int) -> TaskSummary:
        """Generate a comprehensive summary of user's tasks"""
        # Get all pending tasks
        all_tasks = DataFetcher.get_tasks(db, user_id)
        pending_tasks = [t for t in all_tasks if t.status == TaskStatus.PENDING]
        
        # Get overdue tasks
        overdue_tasks = DataFetcher.get_overdue_tasks(db, user_id)
        
        # Get high priority tasks (due within 48 hours)
        high_priority_tasks = DataFetcher.get_high_priority_tasks(db, user_id, hours=48)
        
        # Count tasks by source
        tasks_by_source = {}
        for task in pending_tasks:
            source = task.source_type.value
            tasks_by_source[source] = tasks_by_source.get(source, 0) + 1
        
        # Update overdue task statuses
        for task in overdue_tasks:
            if task.status == TaskStatus.PENDING:
                task.status = TaskStatus.OVERDUE
                db.commit()
        
        # Sort tasks: overdue first, then by due date, then by priority
        sorted_tasks = sorted(
            pending_tasks + overdue_tasks,
            key=lambda t: (
                0 if t.status == TaskStatus.OVERDUE else 1,  # Overdue first
                t.due_date if t.due_date else datetime.max,  # Then by due date
                -t.priority  # Then by priority (descending)
            )
        )
        
        # Convert to response format
        task_responses = [TaskResponse.model_validate(task) for task in sorted_tasks]
        
        return TaskSummary(
            total_tasks=len(all_tasks),
            pending_tasks=len(pending_tasks),
            overdue_tasks=len(overdue_tasks),
            high_priority_tasks=len(high_priority_tasks),
            tasks_by_source=tasks_by_source,
            tasks=task_responses
        )
    
    @staticmethod
    def get_plain_language_summary(db: Session, user_id: int) -> str:
        """Generate a plain language summary of tasks"""
        summary = TaskSummarizer.summarize_tasks(db, user_id)
        
        parts = []
        
        # Overdue tasks
        if summary.overdue_tasks > 0:
            parts.append(f"{summary.overdue_tasks} overdue task{'s' if summary.overdue_tasks > 1 else ''}")
        
        # High priority tasks
        if summary.high_priority_tasks > 0:
            parts.append(f"{summary.high_priority_tasks} task{'s' if summary.high_priority_tasks > 1 else ''} due within 48 hours")
        
        # Total pending
        if summary.pending_tasks > 0:
            parts.append(f"{summary.pending_tasks} pending task{'s' if summary.pending_tasks > 1 else ''} total")
        
        # Tasks by source
        if summary.tasks_by_source:
            source_parts = []
            for source, count in summary.tasks_by_source.items():
                source_name = source.replace("_", " ").title()
                source_parts.append(f"{count} from {source_name}")
            if source_parts:
                parts.append("Tasks: " + ", ".join(source_parts))
        
        if not parts:
            return "No pending tasks. You're all caught up!"
        
        return ". ".join(parts) + "."
    
    @staticmethod
    def categorize_tasks_by_type(tasks: List[Task]) -> Dict[TaskType, List[Task]]:
        """Categorize tasks by type"""
        categorized = {}
        for task in tasks:
            task_type = task.task_type
            if task_type not in categorized:
                categorized[task_type] = []
            categorized[task_type].append(task)
        return categorized
    
    @staticmethod
    def get_weekly_summary(db: Session, user_id: int) -> Dict[str, Any]:
        """Get tasks grouped by week"""
        all_tasks = DataFetcher.get_tasks(db, user_id, status=TaskStatus.PENDING)
        
        now = datetime.now(timezone.utc)
        this_week = []
        next_week = []
        later = []
        
        for task in all_tasks:
            if not task.due_date:
                later.append(task)
                continue
            
            try:
                # Handle timezone-aware and naive datetimes
                due_date = task.due_date
                if due_date.tzinfo is None:
                    due_date = due_date.replace(tzinfo=timezone.utc)
                
                delta = due_date - now
                days_until = delta.days
                
                if days_until < 0:
                    this_week.append(task)  # Overdue
                elif days_until < 7:
                    this_week.append(task)
                elif days_until < 14:
                    next_week.append(task)
                else:
                    later.append(task)
            except Exception:
                later.append(task)
        
        return {
            "this_week": [TaskResponse.model_validate(t) for t in this_week],
            "next_week": [TaskResponse.model_validate(t) for t in next_week],
            "later": [TaskResponse.model_validate(t) for t in later]
        }

