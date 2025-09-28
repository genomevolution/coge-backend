from repository.db import DB
from model.file import File
from model.genomeFile import GenomeFile
from model.annotation import Annotation
from model.annotationFile import AnnotationFile
from model.exceptions.entityNotFoundException import EntityNotFoundException
from sqlmodel import SQLModel
from datetime import datetime
import uuid
import json


class FileRepository:
    """Repository for handling file-related database operations"""
    
    def __init__(self, db: DB):
        self.db = db
    
    def create_file(self, file_path: str, metadata: dict = None) -> File:
        """Create a new file record in the database"""
        file_id = str(uuid.uuid4())
        current_time = datetime.utcnow()
        
        file_record = File(
            id=file_id,
            path=file_path,
            created_at=current_time,
            updated_at=current_time,
            file_metadata=metadata
        )
        
        query = """
        INSERT INTO files (id, path, created_at, updated_at, file_metadata)
        VALUES (%s, %s, %s, %s, %s)
        """
        params = (
            file_record.id,
            file_record.path,
            file_record.created_at,
            file_record.updated_at,
            json.dumps(file_record.file_metadata) if file_record.file_metadata else None
        )
        
        self.db.executeWithPlaceholders(query, params)
        return file_record
    
    def create_genome_file_link(self, file_id: str, genome_id: str, file_type: str) -> GenomeFile:
        """Create a link between a file and a genome"""
        genome_file_id = str(uuid.uuid4())
        
        genome_file = GenomeFile(
            id=genome_file_id,
            file_fk=file_id,
            genome_fk=genome_id,
            type=file_type
        )
        
        query = """
        INSERT INTO genome_files (id, file_fk, genome_fk, type)
        VALUES (%s, %s, %s, %s)
        """
        params = (
            genome_file.id,
            genome_file.file_fk,
            genome_file.genome_fk,
            genome_file.type
        )
        
        self.db.executeWithPlaceholders(query, params)
        return genome_file
    
    def create_annotation(self, genome_id: str, name: str = None, description: str = None, 
                         public: bool = None, primary_annotation: bool = None) -> str:
        """Create a new annotation record and return the annotation ID"""
        annotation_id = str(uuid.uuid4())
        current_time = datetime.utcnow()
        
        query = """
        INSERT INTO annotations (id, fk_genome, created_at, name, description, public, primary_annotation)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        params = (
            annotation_id,
            genome_id,
            current_time,
            name,
            description,
            public,
            primary_annotation
        )
        
        self.db.executeWithPlaceholders(query, params)
        return annotation_id
    
    def create_annotation_file_link(self, file_id: str, annotation_id: str, file_type: str) -> AnnotationFile:
        """Create a link between a file and an annotation"""
        annotation_file_id = str(uuid.uuid4())
        
        annotation_file = AnnotationFile(
            id=annotation_file_id,
            file_fk=file_id,
            annotation_fk=annotation_id,
            type=file_type
        )
        
        query = """
        INSERT INTO annotation_files (id, file_fk, annotation_fk, type)
        VALUES (%s, %s, %s, %s)
        """
        params = (
            annotation_file.id,
            annotation_file.file_fk,
            annotation_file.annotation_fk,
            annotation_file.type
        )
        
        self.db.executeWithPlaceholders(query, params)
        return annotation_file
    
    def get_file_by_path(self, file_path: str) -> File:
        """Get a file record by its path"""
        query = "SELECT * FROM files WHERE path = %s"
        rows = self.db.fetchTuplesWithPlaceholders(query, (file_path,))
        
        if len(rows) < 1:
            raise EntityNotFoundException("File not found")
        
        row = rows[0]
        return File(
            id=row[0],
            path=row[1],
            created_at=row[2],
            updated_at=row[3],
            file_metadata=json.loads(row[4]) if row[4] else None
        )
    
    def delete_file(self, file_id: str) -> bool:
        """Delete a file record and its links"""
        # Delete genome file links
        self.db.executeWithPlaceholders(
            "DELETE FROM genome_files WHERE file_fk = %s",
            (file_id,)
        )
        
        # Delete annotation file links
        self.db.executeWithPlaceholders(
            "DELETE FROM annotation_files WHERE file_fk = %s",
            (file_id,)
        )
        
        # Delete the file record
        self.db.executeWithPlaceholders(
            "DELETE FROM files WHERE id = %s",
            (file_id,)
        )
        
        return True
