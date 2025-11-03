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

  def getGenomesList(self, prev: str, next: str) -> list[Genome]:
    query = "SELECT * FROM organism_data.genome JOIN core.organism ON organism_data.genome.organism_fk = core.organism.id LIMIT %s;"
    params = (PAGINATION_LIMIT,)
    if next is not None:
      query = "SELECT * FROM organism_data.genome JOIN core.organism ON organism_data.genome.organism_fk = core.organism.id WHERE organism_data.genome.id > %s LIMIT %s;"
      params = (next, PAGINATION_LIMIT)
    elif prev is not None:
      query = "SELECT * FROM organism_data.genome JOIN core.organism ON organism_data.genome.organism_fk = core.organism.id WHERE organism_data.genome.id < %s ORDER BY organism_data.genome.id DESC LIMIT %s;"
      params = (prev, PAGINATION_LIMIT)
    rows = self.db.fetchTuplesWithPlaceholders(query, params)
    if prev is not None:
      rows.reverse()

    return [
      Genome(result = r)
      for r in rows]

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
    