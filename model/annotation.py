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

    def __init__(self, result: tuple):
    # ANNOTATIONS
    # |0:id|1:fk_genome|2:created_at|3:name|4:description|5:public|6:primary_annotation
      self.id = result[0] # id
      self.fk_genome = result[1] # fk_genome
      self.created_at = result[2] # created_at
      self.name = result[3] # name
      self.description = result[4] # description
      self.public = result[5] # public
      self.primary_annotation = result[6] # primary_annotation
