import asyncio
import logging
from typing import Optional, Set

from config import config
from repository.blast import BlastRepository
from service.blast import BlastCoordinatorService


logger = logging.getLogger(__name__)


class BlastMonitorService:
    def __init__(self, repository: BlastRepository, coordinator: BlastCoordinatorService, check_interval_seconds: int = 2):
        self.repository = repository
        self.coordinator = coordinator
        self.check_interval_seconds = check_interval_seconds
        self.running = False
        self.task: Optional[asyncio.Task] = None
        self.in_flight: Set[asyncio.Task] = set()

    async def start(self):
        if self.running:
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
        if self.in_flight:
            await asyncio.gather(*self.in_flight, return_exceptions=True)

    async def _monitor_loop(self):
        while self.running:
            try:
                self._discard_completed_tasks()
                available = max(config.BLAST_MAX_CONCURRENT_JOBS - len(self.in_flight), 0)
                for _ in range(available):
                    job_id = self.repository.claim_next_job()
                    if not job_id:
                        break
                    task = asyncio.create_task(asyncio.to_thread(self.coordinator.process_job, job_id))
                    self.in_flight.add(task)
                for job_id in self.repository.delete_expired_jobs():
                    logger.info("Expired BLAST job %s removed", job_id)
            except Exception:
                logger.exception("BLAST monitor failed")
            await asyncio.sleep(self.check_interval_seconds)

    def _discard_completed_tasks(self):
        completed = {task for task in self.in_flight if task.done()}
        for task in completed:
            self.in_flight.discard(task)
            try:
                task.result()
            except Exception:
                logger.exception("BLAST worker task failed")
