from repository.db import DB
from model.exceptions.entity_not_found import EntityNotFoundException
from model import Annotation, AnnotationFile, Genome
from sqlalchemy.orm import joinedload
from datetime import datetime
import uuid

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

  def create_annotation(
    self,
    genome_id: str,
    name: str,
    description: str,
    public: bool,
    primary_annotation: bool
  ):
    session = self.db.get_session()

    try:
      genome = session.query(Genome).filter(Genome.id == genome_id).first()
      if genome is None:
        raise EntityNotFoundException("Genome not found")

      annotation = Annotation(
        id=str(uuid.uuid4()),
        fk_genome=genome_id,
        created_at=datetime.utcnow(),
        name=name,
        description=description,
        public=public,
        primary_annotation=primary_annotation
      )

      session.add(annotation)
      session.commit()
      session.refresh(annotation)

      return annotation

    finally:
      session.close()
