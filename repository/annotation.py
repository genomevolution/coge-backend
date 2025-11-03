from repository.db import DB
from model.exceptions.entityNotFoundException import EntityNotFoundException
from model import Annotation, AnnotationFile
from sqlalchemy.orm import joinedload

class AnnotationRepository:
  def __init__(self, db: DB):
    self.db = db

  def getAnnotationById(self, id: str):
    session = self.db.getSession()
    
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
