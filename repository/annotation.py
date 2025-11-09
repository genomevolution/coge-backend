from repository.db import DB
from model.exceptions.entity_not_found import EntityNotFoundException
from model import Annotation, AnnotationFile
from sqlalchemy.orm import joinedload

class AnnotationRepository:
  def __init__(self, db: DB):
    self.db = db

  def get_annotation_by_id(self, id: str):
    session = self.db.get_session()
    
    try:
      annotation = (
        session.query(Annotation)
        .options(
          joinedload(Annotation.annotation_files).joinedload(AnnotationFile.file)
        )
        .filter(Annotation.id == id)
        .first()
      )
      
      if annotation is None:
        raise EntityNotFoundException("Annotation not found")
      
      return annotation
    
    finally:
      session.close()
