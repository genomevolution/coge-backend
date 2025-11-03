from sqlalchemy import Column, String, ForeignKey, TIMESTAMP
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from model.base_alchemy import Base


class OrganismAlchemy(Base):
    __tablename__ = 'organism'
    __table_args__ = {'schema': 'core'}

    id = Column(String(36), primary_key=True)
    name = Column(String(256), nullable=False)
    user_fk = Column(String(36), ForeignKey('auth.users.id'))
    tax_id = Column(String(36), nullable=False)
    organism_metadata = Column('metadata', JSONB)
    created_at = Column(TIMESTAMP(timezone=True))
    species_name = Column(String(256))

    user = relationship("UserAlchemy", back_populates="organisms", lazy='noload')
    genomes = relationship("GenomeAlchemy", back_populates="organism", lazy='noload')

    def to_dict(self, include_genomes=False):
        result = {
            "id": self.id,
            "name": self.name,
            "taxId": self.tax_id,
            "metadata": self.organism_metadata,
            "createdAt": self.created_at.isoformat() if self.created_at else None,
            "speciesName": self.species_name
        }
        
        if include_genomes and self.genomes:
            result["genomes"] = [genome.to_dict(include_organism=False) for genome in self.genomes]
        
        return result

