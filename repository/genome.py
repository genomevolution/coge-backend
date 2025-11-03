from repository.db import DB
from model.genome import Genome
from model.annotationEntity import AnnotationEntity
from model.exceptions.entityNotFoundException import EntityNotFoundException
from model.paginable import PAGINATION_LIMIT
from model import GenomeAlchemy, GenomeFileAlchemy, AnnotationAlchemy, AnnotationFileAlchemy
from sqlalchemy.orm import joinedload

class GenomeRepository:
  def __init__(self, db: DB):
    self.db = db

  def getGenomes(self, prev: str, next: str) -> list:
    session = self.db.getAlchemySession()
    
    try:
      query = (
        session.query(GenomeAlchemy)
        .options(
          joinedload(GenomeAlchemy.organism),
          joinedload(GenomeAlchemy.source),
          joinedload(GenomeAlchemy.genome_files).joinedload(GenomeFileAlchemy.file),
          joinedload(GenomeAlchemy.annotations)
            .joinedload(AnnotationAlchemy.annotation_files)
            .joinedload(AnnotationFileAlchemy.file)
        )
        .order_by(GenomeAlchemy.id)
      )
      
      if next is not None:
        query = query.filter(GenomeAlchemy.id > next)
      elif prev is not None:
        query = (
          query.filter(GenomeAlchemy.id < prev)
          .order_by(GenomeAlchemy.id.desc())
        )
      
      genomes = query.limit(PAGINATION_LIMIT).all()
      
      if prev is not None:
        genomes.reverse()
      
      return genomes
    
    finally:
      session.close()

  def getGenomeById(self, id: str):
    session = self.db.getAlchemySession()
    
    try:
      genome = (
        session.query(GenomeAlchemy)
        .options(
          joinedload(GenomeAlchemy.organism),
          joinedload(GenomeAlchemy.source),
          joinedload(GenomeAlchemy.genome_files).joinedload(GenomeFileAlchemy.file),
          joinedload(GenomeAlchemy.annotations)
            .joinedload(AnnotationAlchemy.annotation_files)
            .joinedload(AnnotationFileAlchemy.file)
        )
        .filter(GenomeAlchemy.id == id)
        .first()
      )
      
      if genome is None:
        raise EntityNotFoundException("Genome not found")
      
      return genome
    
    finally:
      session.close()
    