from sqlalchemy import Column, String, Boolean, ForeignKey, TIMESTAMP
from sqlalchemy.orm import relationship
from model.db.base import Base

class Annotation(Base):
    __tablename__ = 'annotations'
    __table_args__ = {'schema': 'organism_data'}

    id = Column(String(36), primary_key=True)
    fk_genome = Column(String(36), ForeignKey('organism_data.genome.id'), nullable=False)
    created_at = Column(TIMESTAMP(timezone=True))
    name = Column(String(256))
    description = Column(String(1024))
    public = Column(Boolean)
    primary_annotation = Column(Boolean)

    genome = relationship("Genome", back_populates="annotations")
    annotation_files = relationship("AnnotationFile", back_populates="annotation", lazy='noload')

    def to_dict(self, include_files=False):
        result = {
            "id": self.id,
            "createdAt": self.created_at.isoformat() if self.created_at else None,
            "name": self.name,
            "description": self.description,
            "public": self.public,
            "primaryAnnotation": self.primary_annotation
        }
        
        if include_files and self.annotation_files:
            result["files"] = [af.to_dict() for af in self.annotation_files]
        
        return result
