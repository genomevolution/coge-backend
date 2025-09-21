from sqlmodel import SQLModel, Field, JSON, Column
from typing import Optional
from datetime import datetime


class File(SQLModel, table=True):
    """Model representing a file stored in MinIO"""
    
    id: str = Field(primary_key=True, max_length=36)
    path: str = Field(max_length=256, index=True)
    created_at: Optional[datetime] = Field(default=None)
    updated_at: Optional[datetime] = Field(default=None)
    file_metadata: Optional[dict] = Field(default=None, sa_column=Column(JSON))
