from sqlalchemy import Column, String, TIMESTAMP
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from model.base import Base

class File(Base):
    __tablename__ = 'files'
    __table_args__ = {'schema': 'data_files'}

    id = Column(String(36), primary_key=True)
    path = Column(String(256), nullable=False)
    created_at = Column(TIMESTAMP(timezone=True))
    updated_at = Column(TIMESTAMP(timezone=True))
    file_metadata = Column(JSONB)

    genome_files = relationship("GenomeFile", back_populates="file", lazy='noload')
    annotation_files = relationship("AnnotationFile", back_populates="file", lazy='noload')

    def to_dict(self):
        return {
            "id": self.id,
            "path": self.path,
            "createdAt": self.created_at.isoformat() if self.created_at else None,
            "updatedAt": self.updated_at.isoformat() if self.updated_at else None,
            "metadata": self.file_metadata
        }
