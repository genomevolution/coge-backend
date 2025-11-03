from sqlalchemy import Column, String, ForeignKey
from sqlalchemy.orm import relationship
from model.base import Base

class AnnotationFile(Base):
    __tablename__ = 'annotation_files'
    __table_args__ = {'schema': 'data_files'}

    id = Column(String(36), primary_key=True)
    file_fk = Column(String(36), ForeignKey('data_files.files.id'), nullable=False)
    annotation_fk = Column(String(36), ForeignKey('organism_data.annotations.id'), nullable=False)
    type = Column(String(256), nullable=False)

    file = relationship("File", back_populates="annotation_files")
    annotation = relationship("Annotation", back_populates="annotation_files")

    def to_dict(self, include_file=True):
        result = {
            "id": self.id,
            "type": self.type
        }
        
        if include_file and self.file:
            result["file"] = self.file.to_dict()
        
        return result
