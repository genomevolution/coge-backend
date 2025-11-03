from repository.db import DB
from model.organism import Organism
from model.exceptions.entityNotFoundException import EntityNotFoundException
from model.paginable import PAGINATION_LIMIT
from model.genome import Genome
from model import OrganismAlchemy, GenomeAlchemy, GenomeFileAlchemy
from sqlalchemy.orm import joinedload

class OrganismRepository:
  def __init__(self, db: DB):
    self.db = db

  def getOrganismsList(self, prev: str, next: str) -> list[Organism]:
    query = "SELECT * FROM core.organism LIMIT %s;"
    params = (PAGINATION_LIMIT,)
    if next is not None:
      query = "SELECT * FROM core.organism WHERE id > %s LIMIT %s;"
      params = (next, PAGINATION_LIMIT)
    elif prev is not None:
      query = "SELECT * FROM core.organism WHERE id < %s ORDER BY id DESC LIMIT %s;"
      params = (prev, PAGINATION_LIMIT)
    rows = self.db.fetchTuplesWithPlaceholders(query, params)
    if prev is not None:
      rows.reverse()
    return [
      Organism(result = r)
      for r in rows]

  def getOrganismById(self, id: str):
    session = self.db.getAlchemySession()
    
    try:
      organism = (
        session.query(OrganismAlchemy)
        .options(
          joinedload(OrganismAlchemy.genomes).joinedload(GenomeAlchemy.annotations),
          joinedload(OrganismAlchemy.genomes).joinedload(GenomeAlchemy.source),
          joinedload(OrganismAlchemy.genomes).joinedload(GenomeAlchemy.genome_files).joinedload(GenomeFileAlchemy.file)
        )
        .filter(OrganismAlchemy.id == id)
        .first()
      )
      
      if organism is None:
        raise EntityNotFoundException("Organism not found")
      
      return organism
    
    finally:
      session.close()
