from sqlalchemy import Column, String, ForeignKey
from sqlalchemy.orm import relationship
from model.db.base import Base

class GenomeFile(Base):
    __tablename__ = 'genome_files'
    __table_args__ = {'schema': 'data_files'}

    id = Column(String(36), primary_key=True)
    file_fk = Column(String(36), ForeignKey('data_files.files.id'), nullable=False)
    genome_fk = Column(String(36), ForeignKey('organism_data.genome.id'), nullable=False)
    type = Column(String(256), nullable=False)

    file = relationship("File", back_populates="genome_files")
    genome = relationship("Genome", back_populates="genome_files")

    def to_dict(self, include_file=True):
        result = {
            "id": self.id,
            "type": self.type
        }
        
        if include_file and self.file:
            result["file"] = self.file.to_dict()
        
        return result
