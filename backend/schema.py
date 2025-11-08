from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text, Enum as SQLEnum
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.sql import func
from pydantic import BaseModel, EmailStr
from datetime import datetime
from enum import Enum
from typing import Optional
import enum

Base = declarative_base()

# Enums
class TaskStatus(str, enum.Enum):
    PENDING = "pending"
    COMPLETE = "complete"
    OVERDUE = "overdue"

class TaskType(str, enum.Enum):
    ASSIGNMENT = "assignment"
    MEETING = "meeting"
    INTERNSHIP = "internship"
    MANUAL = "manual"
    EMAIL = "email"

class SourceType(str, enum.Enum):
    CANVAS = "canvas"
    OUTLOOK = "outlook"
    GOOGLE_CALENDAR = "google_calendar"
    HANDSHAKE = "handshake"
    MANUAL = "manual"

# Database Models
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, nullable=False, unique=True, index=True)
    name = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    tokens = relationship("OAuthToken", back_populates="user", cascade="all, delete-orphan")
    tasks = relationship("Task", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User id={self.id} email={self.email} name={self.name}>"


class OAuthToken(Base):
    __tablename__ = "oauth_tokens"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    source_type = Column(SQLEnum(SourceType), nullable=False)
    access_token = Column(Text, nullable=False)  # Encrypted in production
    refresh_token = Column(Text, nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    token_type = Column(String, default="Bearer")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="tokens")

    def __repr__(self):
        return f"<OAuthToken id={self.id} user_id={self.user_id} source={self.source_type}>"


class Task(Base):
    __tablename__ = "tasks"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    task_type = Column(SQLEnum(TaskType), nullable=False)
    status = Column(SQLEnum(TaskStatus), default=TaskStatus.PENDING)
    source_type = Column(SQLEnum(SourceType), nullable=False)
    source_id = Column(String, nullable=True)  # External ID from source
    due_date = Column(DateTime(timezone=True), nullable=True)
    start_date = Column(DateTime(timezone=True), nullable=True)
    priority = Column(Integer, default=0)  # Higher number = higher priority
    task_metadata = Column(Text, nullable=True)  # JSON string for additional data
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="tasks")

    def __repr__(self):
        return f"<Task id={self.id} title={self.title} status={self.status}>"


# Pydantic Schemas for API
class UserCreate(BaseModel):
    email: EmailStr
    name: str

class UserResponse(BaseModel):
    id: int
    email: str
    name: str
    created_at: datetime

    class Config:
        from_attributes = True


class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = None
    task_type: TaskType
    due_date: Optional[datetime] = None
    start_date: Optional[datetime] = None
    priority: int = 0

class TaskUpdate(BaseModel):
    status: Optional[TaskStatus] = None
    title: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[int] = None

class TaskResponse(BaseModel):
    id: int
    user_id: int
    title: str
    description: Optional[str]
    task_type: TaskType
    status: TaskStatus
    source_type: SourceType
    source_id: Optional[str]
    due_date: Optional[datetime]
    start_date: Optional[datetime]
    priority: int
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


class OAuthTokenCreate(BaseModel):
    source_type: SourceType
    access_token: str
    refresh_token: Optional[str] = None
    expires_at: Optional[datetime] = None

class OAuthTokenResponse(BaseModel):
    id: int
    user_id: int
    source_type: SourceType
    expires_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


class TaskSummary(BaseModel):
    total_tasks: int
    pending_tasks: int
    overdue_tasks: int
    high_priority_tasks: int
    tasks_by_source: dict[str, int]
    tasks: list[TaskResponse]