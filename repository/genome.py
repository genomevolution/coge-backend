from repository.db import DB
from model.exceptions.entityNotFoundException import EntityNotFoundException
from model.paginable import PAGINATION_LIMIT
from model import Genome, GenomeFile, Annotation, AnnotationFile
from sqlalchemy.orm import joinedload

class GenomeRepository:
  def __init__(self, db: DB):
    self.db = db

  def getGenomes(self, prev: str, next: str) -> list:
    session = self.db.getSession()
    
    try:
      query = (
        session.query(Genome)
        .options(
          joinedload(Genome.organism),
          joinedload(Genome.source),
          joinedload(Genome.genome_files).joinedload(GenomeFile.file),
          joinedload(Genome.annotations)
            .joinedload(Annotation.annotation_files)
            .joinedload(AnnotationFile.file)
        )
        .order_by(Genome.id)
      )
      
      if next is not None:
        query = query.filter(Genome.id > next)
      elif prev is not None:
        query = (
          query.filter(Genome.id < prev)
          .order_by(Genome.id.desc())
        )
      
      genomes = query.limit(PAGINATION_LIMIT).all()
      
      if prev is not None:
        genomes.reverse()
      
      return genomes
    
    finally:
      session.close()

  def getGenomeById(self, id: str):
    session = self.db.getSession()
    
    try:
      genome = (
        session.query(Genome)
        .options(
          joinedload(Genome.organism),
          joinedload(Genome.source),
          joinedload(Genome.genome_files).joinedload(GenomeFile.file),
          joinedload(Genome.annotations)
            .joinedload(Annotation.annotation_files)
            .joinedload(AnnotationFile.file)
        )
        .filter(Genome.id == id)
        .first()
      )
      
      if genome is None:
        raise EntityNotFoundException("Genome not found")
      
      return genome
    
    finally:
      session.close()
    