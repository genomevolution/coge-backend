from sqlmodel import SQLModel, Field, ForeignKey
from typing import Optional


class AnnotationFile(SQLModel, table=True):
    """Model representing the relationship between files and annotations"""
    
    id: str = Field(primary_key=True, max_length=36)
    file_fk: str = Field(foreign_key="file.id", max_length=36)
    annotation_fk: str = Field(foreign_key="annotation.id", max_length=36)
    type: str = Field(max_length=256)
