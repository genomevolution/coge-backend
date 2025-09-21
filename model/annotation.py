from sqlmodel import SQLModel, Field, ForeignKey
from typing import Optional
from datetime import datetime


class Annotation(SQLModel, table=True):
    """Model representing an annotation for a genome"""
    
    id: str = Field(primary_key=True, max_length=36)
    fk_genome: str = Field(foreign_key="genome.id", max_length=36)
    created_at: Optional[datetime] = Field(default=None)
    name: Optional[str] = Field(default=None, max_length=256)
    description: Optional[str] = Field(default=None, max_length=1024)
    public: Optional[bool] = Field(default=None)
    primary_annotation: Optional[bool] = Field(default=None)
