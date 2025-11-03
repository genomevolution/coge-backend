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

  def getOrganisms(self, prev: str, next: str) -> list:
    session = self.db.getAlchemySession()
    
    try:
      query = (
        session.query(OrganismAlchemy)
        .options(joinedload(OrganismAlchemy.genomes))
        .order_by(OrganismAlchemy.id)
      )
      
      if next is not None:
        query = query.filter(OrganismAlchemy.id > next)
      elif prev is not None:
        query = (
          query.filter(OrganismAlchemy.id < prev)
          .order_by(OrganismAlchemy.id.desc())
        )
      
      organisms = query.limit(PAGINATION_LIMIT).all()
      
      if prev is not None:
        organisms.reverse()
      
      return organisms
    
    finally:
      session.close()

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
