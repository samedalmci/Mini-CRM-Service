
from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(unique=True)
    email: Optional[str] = None
    full_name: Optional[str] = None
    hashed_password: str
    role: str = Field(default="AGENT")  # ADMIN veya AGENT
    disabled: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.now)

class Note(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    raw_text: str
    summary: Optional[str] = None
    status: str = Field(default="queued")  # queued, processing, done, failed
    user_id: int = Field(foreign_key="user.id")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)