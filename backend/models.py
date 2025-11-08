from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from schema import Base, User, Task, OAuthToken, TaskStatus, TaskType, SourceType
from datetime import datetime, timedelta
from typing import Optional, List
import os

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:password@localhost:5432/app_db")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def create_db():
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class DataFetcher:
    @classmethod
    def get_users(cls, db):
        users = db.query(User).all()
        return users
    
    @classmethod
    def get_user(cls, db, user_id: int):
        user = db.query(User).filter(User.id == user_id).first()
        return user
    
    @classmethod
    def get_user_by_email(cls, db, email: str):
        user = db.query(User).filter(User.email == email).first()
        return user
    
    @classmethod
    def create_user(cls, db, email: str, name: str):
        user = User(email=email, name=name)
        db.add(user)
        db.commit()
        db.refresh(user)
        return user
    
    @classmethod
    def get_tasks(cls, db, user_id: int, status: Optional[TaskStatus] = None):
        query = db.query(Task).filter(Task.user_id == user_id)
        if status:
            query = query.filter(Task.status == status)
        return query.order_by(Task.due_date.asc(), Task.priority.desc()).all()
    
    @classmethod
    def get_task(cls, db, task_id: int, user_id: int):
        task = db.query(Task).filter(Task.id == task_id, Task.user_id == user_id).first()
        return task
    
    @classmethod
    def create_task(cls, db, user_id: int, title: str, description: Optional[str], 
                   task_type: TaskType, source_type: SourceType, 
                   due_date: Optional[datetime] = None, start_date: Optional[datetime] = None,
                   priority: int = 0, source_id: Optional[str] = None, task_metadata: Optional[str] = None):
        task = Task(
            user_id=user_id,
            title=title,
            description=description,
            task_type=task_type,
            source_type=source_type,
            due_date=due_date,
            start_date=start_date,
            priority=priority,
            source_id=source_id,
            task_metadata=task_metadata
        )
        db.add(task)
        db.commit()
        db.refresh(task)
        return task
    
    @classmethod
    def update_task_status(cls, db, task_id: int, user_id: int, status: TaskStatus):
        task = cls.get_task(db, task_id, user_id)
        if task:
            task.status = status
            db.commit()
            db.refresh(task)
        return task
    
    @classmethod
    def get_oauth_token(cls, db, user_id: int, source_type: SourceType):
        token = db.query(OAuthToken).filter(
            OAuthToken.user_id == user_id,
            OAuthToken.source_type == source_type
        ).first()
        return token
    
    @classmethod
    def upsert_oauth_token(cls, db, user_id: int, source_type: SourceType, 
                          access_token: str, refresh_token: Optional[str] = None,
                          expires_at: Optional[datetime] = None):
        token = cls.get_oauth_token(db, user_id, source_type)
        if token:
            token.access_token = access_token
            token.refresh_token = refresh_token
            token.expires_at = expires_at
        else:
            token = OAuthToken(
                user_id=user_id,
                source_type=source_type,
                access_token=access_token,
                refresh_token=refresh_token,
                expires_at=expires_at
            )
            db.add(token)
        db.commit()
        db.refresh(token)
        return token
    
    @classmethod
    def get_overdue_tasks(cls, db, user_id: int):
        from datetime import timezone
        now = datetime.now(timezone.utc)
        return db.query(Task).filter(
            Task.user_id == user_id,
            Task.status == TaskStatus.PENDING,
            Task.due_date < now
        ).all()
    
    @classmethod
    def get_high_priority_tasks(cls, db, user_id: int, hours: int = 48):
        from datetime import timezone
        now = datetime.now(timezone.utc)
        deadline = now + timedelta(hours=hours)
        return db.query(Task).filter(
            Task.user_id == user_id,
            Task.status == TaskStatus.PENDING,
            Task.due_date >= now,
            Task.due_date <= deadline
        ).all()