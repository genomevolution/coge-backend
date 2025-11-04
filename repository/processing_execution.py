import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy import desc
from model.db.processing_execution import ProcessingExecution
from repository.db import DB

STATUS_RUNNING = 'RUNNING'

class ProcessingExecutionRepository:
    def __init__(self, db: DB):
        self.db = db
    
    def create_execution(
        self,
        genome_id: str,
        execution_type: str,
        pid: int,
        profile: str,
        fasta_path: str,
        output_dir: str,
        log_file: str,
        metadata: Optional[Dict[str, Any]] = None,
        execution_id: Optional[str] = None
    ) -> ProcessingExecution:
        if execution_id is None:
            execution_id = str(uuid.uuid4())
        
        now = datetime.utcnow()
        
        execution = ProcessingExecution(
            id=execution_id,
            genome_id=genome_id,
            execution_type=execution_type,
            status=STATUS_RUNNING,
            progress=0,
            pid=pid,
            profile=profile,
            fasta_path=fasta_path,
            output_dir=output_dir,
            log_file=log_file,
            execution_metadata=metadata,
            started_at=now,
            created_at=now,
            updated_at=now
        )
        
        with self.db.get_session() as session:
            session.add(execution)
            session.commit()
            return execution
    
    def get_execution_by_id(self, execution_id: str) -> Optional[ProcessingExecution]:
        with self.db.get_session() as session:
            return session.query(ProcessingExecution).filter(
                ProcessingExecution.id == execution_id
            ).first()
    
    def get_executions_by_genome_id(
        self, 
        genome_id: str, 
        limit: int = 10
    ) -> List[ProcessingExecution]:
        with self.db.get_session() as session:
            return session.query(ProcessingExecution).filter(
                ProcessingExecution.genome_id == genome_id
            ).order_by(desc(ProcessingExecution.created_at)).limit(limit).all()
    
    def get_running_executions(self) -> List[ProcessingExecution]:
        with self.db.get_session() as session:
            return session.query(ProcessingExecution).filter(
                ProcessingExecution.status == STATUS_RUNNING
            ).all()
    
    def update_execution_status(
        self,
        execution_id: str,
        status: str,
        progress: Optional[int] = None,
        error_message: Optional[str] = None
    ) -> Optional[ProcessingExecution]:
        with self.db.get_session() as session:
            execution = session.query(ProcessingExecution).filter(
                ProcessingExecution.id == execution_id
            ).first()
            
            if not execution:
                return None
            
            execution.status = status
            execution.updated_at = datetime.utcnow()
            
            if progress is not None:
                execution.progress = progress
            
            if error_message is not None:
                execution.error_message = error_message
            
            if status in ['COMPLETED', 'FAILED', 'CANCELLED']:
                execution.completed_at = datetime.utcnow()
            
            session.commit()
            return execution
    
    def update_execution_progress(
        self,
        execution_id: str,
        progress: int
    ) -> Optional[ProcessingExecution]:
        with self.db.get_session() as session:
            execution = session.query(ProcessingExecution).filter(
                ProcessingExecution.id == execution_id
            ).first()
            
            if not execution:
                return None
            
            execution.progress = progress
            execution.updated_at = datetime.utcnow()
            session.commit()
            return execution
    
    def update_execution_metadata(
        self,
        execution_id: str,
        metadata: Dict[str, Any]
    ) -> Optional[ProcessingExecution]:
        with self.db.get_session() as session:
            execution = session.query(ProcessingExecution).filter(
                ProcessingExecution.id == execution_id
            ).first()
            
            if not execution:
                return None
            
            if execution.execution_metadata:
                execution.execution_metadata.update(metadata)
            else:
                execution.execution_metadata = metadata
            
            execution.updated_at = datetime.utcnow()
            session.commit()
            return execution
    
    def delete_execution(self, execution_id: str) -> bool:
        with self.db.get_session() as session:
            execution = session.query(ProcessingExecution).filter(
                ProcessingExecution.id == execution_id
            ).first()
            
            if not execution:
                return False
            
            session.delete(execution)
            session.commit()
            return True

