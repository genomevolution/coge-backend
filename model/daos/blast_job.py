from sqlalchemy import Column, Integer, String, Text, TIMESTAMP
from sqlalchemy.dialects.postgresql import JSONB
from model.daos.base import Base


class BlastJob(Base):
    __tablename__ = "blast_jobs"
    __table_args__ = {"schema": "processing"}

    id = Column(String(36), primary_key=True)
    program = Column(String(32), nullable=False)
    status = Column(String(32), nullable=False, default="QUEUED")
    progress = Column(Integer, nullable=False, default=0)
    query_fasta = Column(Text, nullable=False)
    selection = Column(JSONB, nullable=False)
    parameters = Column(JSONB, nullable=False)
    execution_id = Column(String(36))
    result_count = Column(Integer, nullable=False, default=0)
    results = Column(JSONB)
    error_message = Column(Text)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False)
    started_at = Column(TIMESTAMP(timezone=True))
    completed_at = Column(TIMESTAMP(timezone=True))
    expires_at = Column(TIMESTAMP(timezone=True), nullable=False)

    def to_dict(self, include_results: bool = False):
        payload = {
            "id": self.id,
            "program": self.program,
            "status": self.status,
            "progress": self.progress,
            "selection": self.selection,
            "parameters": self.parameters,
            "resultCount": self.result_count,
            "errorMessage": self.error_message,
            "createdAt": self.created_at.isoformat() if self.created_at else None,
            "startedAt": self.started_at.isoformat() if self.started_at else None,
            "completedAt": self.completed_at.isoformat() if self.completed_at else None,
            "expiresAt": self.expires_at.isoformat() if self.expires_at else None,
        }
        if include_results:
            payload["results"] = self.results or []
        return payload
