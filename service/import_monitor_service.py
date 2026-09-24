import asyncio
import logging
from typing import Optional

from repository.data_import import DataImportRepository
from service.import_coordinator import ImportCoordinatorService
from service.import_status import ImportStatus


logger = logging.getLogger(__name__)


class ImportMonitorService:
    def __init__(
        self,
        repository: DataImportRepository,
        coordinator: ImportCoordinatorService,
        check_interval_seconds: int = 2
    ):
        self.repository = repository
        self.coordinator = coordinator
        self.check_interval_seconds = check_interval_seconds
        self.running = False
        self.task: Optional[asyncio.Task] = None

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

    async def _monitor_loop(self):
        while self.running:
            try:
                for data_import in self.repository.get_processable_imports():
                    await asyncio.to_thread(
                        self.coordinator.process_import,
                        data_import
                    )
                await self._cleanup_expired_imports()
            except Exception as error:
                logger.error("Import monitor failed: %s", error, exc_info=True)
            await asyncio.sleep(self.check_interval_seconds)

    async def _cleanup_expired_imports(self):
        for data_import in self.repository.get_expired_action_required():
            await asyncio.to_thread(
                self.coordinator.cleanup_failed_import,
                data_import
            )
            self.repository.update(
                data_import.id,
                status=ImportStatus.CANCELLED.value,
                phase=ImportStatus.CANCELLED.value
            )
        for data_import in self.repository.get_expired_terminal():
            self.repository.delete(data_import.id)
