import asyncio
import logging
from enum import Enum
from typing import Optional
from datetime import datetime
from service.genome_processing_service import GenomeProcessingService
from repository.processing_execution import ProcessingExecutionRepository

logger = logging.getLogger(__name__)

class ExecutionStatus(str, Enum):
    RUNNING = 'RUNNING'
    COMPLETED = 'COMPLETED'
    FAILED = 'FAILED'
    CANCELLED = 'CANCELLED'

class ExecutionMonitorService:
    def __init__(
        self,
        genome_processing_service: GenomeProcessingService,
        processing_execution_repo: ProcessingExecutionRepository,
        check_interval_seconds: int = 60
    ):
        self.genome_processing_service = genome_processing_service
        self.processing_execution_repo = processing_execution_repo
        self.check_interval_seconds = check_interval_seconds
        self.running = False
        self.task: Optional[asyncio.Task] = None
    
    async def start(self):
        if self.running:
            logger.warning("Monitor service already running")
            return
        
        self.running = True
        self.task = asyncio.create_task(self._monitor_loop())
    
    async def stop(self):
        self.running = False
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass

    async def _monitor_loop(self):
        while self.running:
            try:
                await self._check_running_executions()
            except Exception as e:
                logger.error(f"Error in monitor loop: {e}", exc_info=True)
            
            await asyncio.sleep(self.check_interval_seconds)
    
    async def _check_running_executions(self):
        running_executions = self.processing_execution_repo.get_executions_by_status(ExecutionStatus.RUNNING)
        
        if not running_executions:
            return
        
        await self._process_executions(running_executions)
    
    async def _process_executions(self, executions):
        for execution in executions:
            await self._process_single_execution(execution)
    
    async def _process_single_execution(self, execution):
        try:
            status = self.genome_processing_service.get_execution_status(execution.id)
            current_status = status.get('status')
    
            if current_status != ExecutionStatus.RUNNING:
                await self._update_execution_status(execution.id, status, current_status)
                
                if current_status == ExecutionStatus.COMPLETED:
                    await self._finalize_execution(execution.id)
            
        except Exception as e:
            logger.error(f"Error checking execution {execution.id}: {e}", exc_info=True)
    
    async def _update_execution_status(self, execution_id: str, status: dict, current_status: str):
        now = datetime.utcnow()
        completed_at = now if current_status in [ExecutionStatus.COMPLETED, ExecutionStatus.FAILED, ExecutionStatus.CANCELLED] else None
        
        self.processing_execution_repo.update_execution_status(
            execution_id,
            current_status,
            updated_at=now,
            progress=status.get('progress', 0),
            error_message=status.get('error_message'),
            completed_at=completed_at
        )
    
    async def _finalize_execution(self, execution_id: str):
        try:
            result = self.genome_processing_service.finalize_execution(execution_id)
        except Exception as e:
            now = datetime.utcnow()
            self.processing_execution_repo.update_execution_status(
                execution_id,
                ExecutionStatus.FAILED,
                updated_at=now,
                error_message=f"Finalization failed: {str(e)}",
                completed_at=now
            )

