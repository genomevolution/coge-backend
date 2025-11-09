from sqlalchemy import Column, String, Integer, TIMESTAMP, ForeignKey, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from model.daos .base import Base

class ProcessingExecution(Base):
    __tablename__ = 'executions'
    __table_args__ = {'schema': 'processing'}

    id = Column(String(36), primary_key=True)
    genome_id = Column(String(36), ForeignKey('organism_data.genome.id', ondelete='CASCADE'))
    execution_type = Column(String(50), nullable=False, default='GENOME_INDEXING')
    status = Column(String(20), nullable=False, default='PENDING')
    progress = Column(Integer, default=0)
    pid = Column(Integer)
    profile = Column(String(50))
    fasta_path = Column(Text)
    output_dir = Column(Text)
    log_file = Column(Text)
    error_message = Column(Text)
    execution_metadata = Column(JSONB)
    created_at = Column(TIMESTAMP(timezone=True))
    started_at = Column(TIMESTAMP(timezone=True))
    completed_at = Column(TIMESTAMP(timezone=True))
    updated_at = Column(TIMESTAMP(timezone=True))

    genome = relationship("Genome", backref="processing_executions")

    def to_dict(self, include_genome=False):
        result = {
            "id": self.id,
            "genomeId": self.genome_id,
            "executionType": self.execution_type,
            "status": self.status,
            "progress": self.progress,
            "pid": self.pid,
            "profile": self.profile,
            "fastaPath": self.fasta_path,
            "outputDir": self.output_dir,
            "logFile": self.log_file,
            "errorMessage": self.error_message,
            "metadata": self.execution_metadata,
            "createdAt": self.created_at.isoformat() if self.created_at else None,
            "startedAt": self.started_at.isoformat() if self.started_at else None,
            "completedAt": self.completed_at.isoformat() if self.completed_at else None,
            "updatedAt": self.updated_at.isoformat() if self.updated_at else None
        }
        
        if include_genome and self.genome:
            result["genome"] = self.genome.to_dict()
        
        return result

