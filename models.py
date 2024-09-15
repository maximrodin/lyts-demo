# models.py
from typing import Optional
from sqlmodel import SQLModel, Field
from datetime import datetime


class TaskBase(SQLModel):
    """
    Shared properties for a task.
    """
    title: str
    description: Optional[str] = None
    status: str = "pending"
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Task(TaskBase, table=True):
    """
    The Task model represents a task in the database.
    """
    id: Optional[int] = Field(default=None, primary_key=True)


class TaskCreate(TaskBase):
    """
    Properties to receive via API on task creation.
    """
    pass


class TaskRead(TaskBase):
    """
    Properties to return via API on task read.
    """
    id: int
