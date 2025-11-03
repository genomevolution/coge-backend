from sqlalchemy import Column, String
from sqlalchemy.orm import relationship
from model.base import Base

class Source(Base):
    __tablename__ = 'source'
    __table_args__ = {'schema': 'organism_data'}

    id = Column(String(36), primary_key=True)
    name = Column(String(256), nullable=False)

    genomes = relationship("Genome", back_populates="source", lazy='noload')

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name
        }
