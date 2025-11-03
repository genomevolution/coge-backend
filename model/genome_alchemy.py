from sqlalchemy import Column, String, Boolean, ForeignKey, TIMESTAMP
from sqlalchemy.orm import relationship
from model.base_alchemy import Base
from model.paginable import Paginable


class GenomeAlchemy(Base, Paginable):
    __tablename__ = 'genome'
    __table_args__ = {'schema': 'organism_data'}

    id = Column(String(36), primary_key=True)
    organism_fk = Column(String(36), ForeignKey('core.organism.id'), nullable=False)
    created_at = Column(TIMESTAMP(timezone=True))
    name = Column(String(256))
    description = Column(String(1024))
    public = Column(Boolean)
    accesion_id = Column(String(256))
    source_fk = Column(String(36), ForeignKey('organism_data.source.id'))

    organism = relationship("OrganismAlchemy", back_populates="genomes")
    source = relationship("SourceAlchemy", back_populates="genomes", lazy='noload')
    genome_files = relationship("GenomeFileAlchemy", back_populates="genome", lazy='noload')
    annotations = relationship("AnnotationAlchemy", back_populates="genome", lazy='noload')

    def getId(self):
        return self.id

    def to_dict(self, include_organism=True, include_annotations=False, include_files=False, include_source=False):
        result = {
            "id": self.id,
            "createdAt": self.created_at.isoformat() if self.created_at else None,
            "name": self.name,
            "description": self.description,
            "public": self.public,
            "accesionId": self.accesion_id
        }
        
        if include_organism and self.organism:
            result["organism"] = self.organism.to_dict()
        
        if include_source and self.source:
            result["source"] = self.source.to_dict()
        
        if include_annotations and self.annotations:
            result["annotations"] = [annotation.to_dict(include_files=True) for annotation in self.annotations]
        
        if include_files and self.genome_files:
            result["genomeFiles"] = [gf.to_dict() for gf in self.genome_files]
        
        return result
