from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy import desc
from model.daos.processing_execution import ProcessingExecution
from repository.db import DB

class ProcessingExecutionRepository:
    def __init__(self, db: DB):
        self.db = db
    
    def create_execution(
        self,
        execution_id: str,
        genome_id: str,
        execution_type: str,
        status: str,
        progress: int,
        pid: int,
        profile: str,
        original_path: str,
        output_dir: str,
        log_file: str,
        started_at: datetime,
        created_at: datetime,
        updated_at: datetime,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ProcessingExecution:
        try:
            session = self.db.get_session()
            
            execution = ProcessingExecution(
                id=execution_id,
                genome_id=genome_id,
                execution_type=execution_type,
                status=status,
                progress=progress,
                pid=pid,
                profile=profile,
                original_path=original_path,
                output_dir=output_dir,
                log_file=log_file,
                execution_metadata=metadata,
                started_at=started_at,
                created_at=created_at,
                updated_at=updated_at
            )
            
            session.add(execution)
            session.commit()
            return execution
        
        finally:
            session.close()
    
    def get_execution_by_id(self, execution_id: str) -> Optional[ProcessingExecution]:     
        try:
            session = self.db.get_session()
            return session.query(ProcessingExecution).filter(
                ProcessingExecution.id == execution_id
            ).first()
        
        finally:
            session.close()
    
    def get_executions_by_genome_id(
        self, 
        genome_id: str, 
        limit: int = 10
    ) -> List[ProcessingExecution]:
        try:
            session = self.db.get_session()
            return session.query(ProcessingExecution).filter(
                ProcessingExecution.genome_id == genome_id
            ).order_by(desc(ProcessingExecution.created_at)).limit(limit).all()
        
        finally:
            session.close()
    
    def get_executions_by_status(self, status: str) -> List[ProcessingExecution]:
        try:
            session = self.db.get_session()
            return session.query(ProcessingExecution).filter(
                ProcessingExecution.status == status
            ).all()
        
        finally:
            session.close()
    
    def get_executions_by_status_and_type(self, status: str, execution_type: str) -> List[ProcessingExecution]:
        try:
            session = self.db.get_session()
            return session.query(ProcessingExecution).filter(
                ProcessingExecution.status == status,
                ProcessingExecution.execution_type == execution_type
            ).all()
        
        finally:
            session.close()
    
    def update_execution_status(
        self,
        execution_id: str,
        status: str,
        updated_at: datetime,
        progress: Optional[int] = None,
        error_message: Optional[str] = None,
        completed_at: Optional[datetime] = None
    ) -> Optional[ProcessingExecution]:
        try:
            session = self.db.get_session()
            execution = session.query(ProcessingExecution).filter(
                ProcessingExecution.id == execution_id
            ).first()
            
            if not execution:
                return None
            
            self._update_execution_params(
                execution,
                status,
                updated_at,
                progress,
                error_message,
                completed_at
            )
            
            session.commit()
            return execution
        
        finally:
            session.close()
    
    def update_execution_progress(
        self,
        execution_id: str,
        progress: int,
        updated_at: datetime
    ) -> Optional[ProcessingExecution]:
        try:
            session = self.db.get_session()
            execution = session.query(ProcessingExecution).filter(
                ProcessingExecution.id == execution_id
            ).first()
            
            if not execution:
                return None
            
            execution.progress = progress
            execution.updated_at = updated_at
            session.commit()
            return execution
        
        finally:
            session.close()
    
    def update_execution_metadata(
        self,
        execution_id: str,
        metadata: Dict[str, Any],
        updated_at: datetime
    ) -> Optional[ProcessingExecution]:
        try:
            session = self.db.get_session()  
            execution = session.query(ProcessingExecution).filter(
                ProcessingExecution.id == execution_id
            ).first()
            
            if not execution:
                return None
            
            self._update_metadata_params(execution, metadata, updated_at)
            
            session.commit()
            return execution
        
        finally:
            session.close()
    
    def delete_execution(self, execution_id: str) -> bool:
        try:
            session = self.db.get_session()
            execution = session.query(ProcessingExecution).filter(
                ProcessingExecution.id == execution_id
            ).first()
            
            if not execution:
                return False
            
            session.delete(execution)
            session.commit()
            return True
        
        finally:
            session.close()
    
    def _update_execution_params(
        self,
        execution: ProcessingExecution,
        status: str,
        updated_at: datetime,
        progress: Optional[int] = None,
        error_message: Optional[str] = None,
        completed_at: Optional[datetime] = None
    ) -> None:
        execution.status = status
        execution.updated_at = updated_at
        
        if progress is not None:
            execution.progress = progress
        
        if error_message is not None:
            execution.error_message = error_message
        
        if completed_at is not None:
            execution.completed_at = completed_at
    
    def _update_metadata_params(
        self,
        execution: ProcessingExecution,
        metadata: Dict[str, Any],
        updated_at: datetime
    ) -> None:
        if execution.execution_metadata:
            execution.execution_metadata.update(metadata)
        else:
            execution.execution_metadata = metadata
        
        execution.updated_at = updated_at
