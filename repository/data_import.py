from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from sqlalchemy import desc

from model import DataImport
from repository.db import DB
from service.import_status import ACTIVE_IMPORT_STATUSES, ImportStatus


class DataImportRepository:
    def __init__(self, db: DB):
        self.db = db

    def create_import(self, values: Dict[str, Any]) -> DataImport:
        session = self.db.get_session()
        try:
            data_import = DataImport(**values)
            session.add(data_import)
            session.commit()
            session.refresh(data_import)
            return data_import
        finally:
            session.close()

    def get_by_id(self, import_id: str) -> Optional[DataImport]:
        session = self.db.get_session()
        try:
            return session.query(DataImport).filter(DataImport.id == import_id).first()
        finally:
            session.close()

    def get_active_imports(self):
        session = self.db.get_session()
        try:
            return (
                session.query(DataImport)
                .filter(DataImport.status.in_(ACTIVE_IMPORT_STATUSES))
                .order_by(desc(DataImport.created_at))
                .all()
            )
        finally:
            session.close()

    def get_processable_imports(self):
        processable_statuses = (
            ImportStatus.QUEUED.value,
            ImportStatus.VALIDATING_FASTA.value,
            ImportStatus.PROCESSING_FASTA.value,
            ImportStatus.VALIDATING_GFF3.value,
            ImportStatus.PROCESSING_GFF3.value,
            ImportStatus.PUBLISHING.value
        )
        session = self.db.get_session()
        try:
            return (
                session.query(DataImport)
                .filter(DataImport.status.in_(processable_statuses))
                .order_by(DataImport.created_at)
                .all()
            )
        finally:
            session.close()

    def update(self, import_id: str, **values) -> Optional[DataImport]:
        session = self.db.get_session()
        try:
            data_import = session.query(DataImport).filter(DataImport.id == import_id).first()
            if data_import is None:
                return None

            for key, value in values.items():
                setattr(data_import, key, value)
            data_import.updated_at = datetime.utcnow()
            session.commit()
            session.refresh(data_import)
            return data_import
        finally:
            session.close()

    def merge_execution_metadata(self, import_id: str, values: Dict[str, Any]):
        data_import = self.get_by_id(import_id)
        if data_import is None:
            return None
        metadata = dict(data_import.execution_metadata or {})
        metadata.update(values)
        return self.update(import_id, execution_metadata=metadata)

    def get_expired_action_required(self, retention_days: int = 7):
        cutoff = datetime.utcnow() - timedelta(days=retention_days)
        session = self.db.get_session()
        try:
            return (
                session.query(DataImport)
                .filter(
                    DataImport.status == ImportStatus.ACTION_REQUIRED.value,
                    DataImport.updated_at < cutoff
                )
                .all()
            )
        finally:
            session.close()

    def get_expired_terminal(self, retention_days: int = 30):
        cutoff = datetime.utcnow() - timedelta(days=retention_days)
        session = self.db.get_session()
        try:
            return (
                session.query(DataImport)
                .filter(
                    DataImport.status.in_((
                        ImportStatus.PUBLISHED.value,
                        ImportStatus.CANCELLED.value
                    )),
                    DataImport.completed_at < cutoff
                )
                .all()
            )
        finally:
            session.close()

    def delete(self, import_id: str) -> bool:
        session = self.db.get_session()
        try:
            data_import = session.query(DataImport).filter(
                DataImport.id == import_id
            ).first()
            if data_import is None:
                return False
            session.delete(data_import)
            session.commit()
            return True
        finally:
            session.close()
