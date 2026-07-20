from sqlalchemy import Column, Integer, String, TIMESTAMP, Text, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB

from model.daos.base import Base


class DataImport(Base):
    __tablename__ = "imports"
    __table_args__ = {"schema": "processing"}

    id = Column(String(36), primary_key=True)
    mode = Column(String(32), nullable=False)
    status = Column(String(32), nullable=False)
    phase = Column(String(64), nullable=False)
    progress = Column(Integer, nullable=False, default=0)
    payload = Column(JSONB, nullable=False)
    target_organism_id = Column(String(36), ForeignKey("core.organism.id"))
    planned_organism_id = Column(String(36))
    planned_genome_id = Column(String(36))
    planned_annotation_id = Column(String(36))
    fasta_path = Column(Text)
    gff3_path = Column(Text)
    current_execution_id = Column(String(36))
    current_execution_type = Column(String(64))
    execution_metadata = Column(JSONB)
    failed_component = Column(String(32))
    error_message = Column(Text)
    published_entity_id = Column(String(36))
    created_at = Column(TIMESTAMP(timezone=True))
    updated_at = Column(TIMESTAMP(timezone=True))
    completed_at = Column(TIMESTAMP(timezone=True))

    def to_dict(self):
        metadata = self.execution_metadata or {}
        return {
            "id": self.id,
            "mode": self.mode,
            "status": self.status,
            "phase": self.phase,
            "progress": self.progress,
            "payload": self.payload,
            "targetOrganismId": self.target_organism_id,
            "failedComponent": self.failed_component,
            "errorMessage": self.error_message,
            "publishedEntityId": self.published_entity_id,
            "canReplaceFasta": self.failed_component == "FASTA",
            "canReplaceGff3": self.failed_component == "GFF3",
            "canRemoveAnnotation": self.failed_component == "GFF3",
            "createdAt": self.created_at.isoformat() if self.created_at else None,
            "updatedAt": self.updated_at.isoformat() if self.updated_at else None,
            "completedAt": self.completed_at.isoformat() if self.completed_at else None,
            "details": {
                "fastaFileName": metadata.get("fasta_file_name"),
                "gff3FileName": metadata.get("gff3_file_name")
            }
        }
