from repository.db import DB
from model import File, GenomeFile, AnnotationFile
from datetime import datetime
import uuid

class FileRepository:    
    def __init__(self, db: DB):
        self.db = db
    
    def create_file(self, file_path: str, metadata: dict = None) -> File:
        session = self.db.getSession()
        
        try:
            file_id = str(uuid.uuid4())
            current_time = datetime.utcnow()
            
            file_record = File(
                id=file_id,
                path=file_path,
                created_at=current_time,
                updated_at=current_time,
                file_metadata=metadata
            )
            
            session.add(file_record)
            session.commit()
            session.refresh(file_record)
            
            return file_record
        
        finally:
            session.close()
    
    def create_genome_file_link(self, file_id: str, genome_id: str, file_type: str) -> GenomeFile:
        """Create a link between a file and a genome"""
        session = self.db.getSession()
        
        try:
            genome_file_id = str(uuid.uuid4())
            
            genome_file = GenomeFile(
                id=genome_file_id,
                file_fk=file_id,
                genome_fk=genome_id,
                type=file_type
            )
            
            session.add(genome_file)
            session.commit()
            session.refresh(genome_file)
            
            return genome_file
        
        finally:
            session.close()
    
    def create_annotation_file_link(self, file_id: str, annotation_id: str, file_type: str) -> AnnotationFile:
        """Create a link between a file and an annotation"""
        session = self.db.getSession()
        
        try:
            annotation_file_id = str(uuid.uuid4())
            
            annotation_file = AnnotationFile(
                id=annotation_file_id,
                file_fk=file_id,
                annotation_fk=annotation_id,
                type=file_type
            )
            
            session.add(annotation_file)
            session.commit()
            session.refresh(annotation_file)
            
            return annotation_file
        
        finally:
            session.close()
