import asyncio
import logging
from typing import Optional
from datetime import datetime
from service.genome_processing_service import GenomeProcessingService
from repository.processing_execution import ProcessingExecutionRepository

logger = logging.getLogger(__name__)

class ExecutionMonitorService:
    """
    Background service that monitors running executions and automatically
    finalizes them when they complete successfully
    """
    
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
        """Start the monitoring service"""
        if self.running:
            logger.warning("Monitor service already running")
            return
        
        self.running = True
        self.task = asyncio.create_task(self._monitor_loop())
        logger.info("Execution monitor service started")
    
    async def stop(self):
        """Stop the monitoring service"""
        self.running = False
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
        logger.info("Execution monitor service stopped")
    
    async def _monitor_loop(self):
        """Main monitoring loop"""
        logger.info(f"Monitor loop started with check interval: {self.check_interval_seconds}s")
        while self.running:
            try:
                await self._check_running_executions()
            except Exception as e:
                logger.error(f"Error in monitor loop: {e}", exc_info=True)
            
            await asyncio.sleep(self.check_interval_seconds)
    
    async def _check_running_executions(self):
        """
        Check running executions and finalize completed ones.
        The lifecycle thread updates metadata.json when Nextflow completes,
        so we just need to check for status changes.
        """
        running_executions = self.processing_execution_repo.get_executions_by_status('RUNNING')
        
        if not running_executions:
            logger.debug("No running executions found")
            return
        
        logger.info(f"Monitor check: Found {len(running_executions)} running execution(s)")
        
        for execution in running_executions:
            try:
                logger.info(f"Checking execution {execution.id}")
                # Get status (reads metadata.json, very fast)
                status = self.genome_processing_service.get_execution_status(execution.id)
                current_status = status.get('status')
                logger.info(f"Execution {execution.id} status: {current_status}")
                
                # Update database with current status
                if current_status != 'RUNNING':
                    logger.info(f"Execution {execution.id} changed from RUNNING to {current_status}")
                    
                    now = datetime.utcnow()
                    completed_at = now if current_status in ['COMPLETED', 'FAILED', 'CANCELLED'] else None
                    
                    self.processing_execution_repo.update_execution_status(
                        execution.id,
                        current_status,
                        updated_at=now,
                        progress=status.get('progress', 0),
                        error_message=status.get('error_message'),
                        completed_at=completed_at
                    )
                    
                    # If completed successfully, finalize and upload files
                    if current_status == 'COMPLETED':
                        logger.info(f"Starting finalization for {execution.id}")
                        await self._finalize_execution(execution.id)
                
            except Exception as e:
                logger.error(f"Error checking execution {execution.id}: {e}", exc_info=True)
    
    async def _finalize_execution(self, execution_id: str):
        """Finalize a completed execution"""
        try:
            result = self.genome_processing_service.finalize_execution(execution_id)
            logger.info(
                f"Successfully finalized execution {execution_id}. "
                f"Uploaded files: {list(result.get('uploaded_files', {}).keys())}"
            )
        except Exception as e:
            logger.error(f"Failed to finalize execution {execution_id}: {e}", exc_info=True)
            now = datetime.utcnow()
            self.processing_execution_repo.update_execution_status(
                execution_id,
                'FAILED',
                updated_at=now,
                error_message=f"Finalization failed: {str(e)}",
                completed_at=now
            )

