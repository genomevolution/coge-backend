from repository.db import DB
from model.exceptions.entity_not_found import EntityNotFoundException
from model.dto.paginable import PAGINATION_LIMIT
from model import Organism, Genome, GenomeFile
from sqlalchemy.orm import joinedload
from datetime import datetime
import uuid

class OrganismRepository:
  def __init__(self, db: DB):
    self.db = db

  def get_organisms(self, prev: str, next: str) -> list:
    session = self.db.get_session()
    
    try:
      query = (
        session.query(Organism)
        .options(joinedload(Organism.genomes))
        .order_by(Organism.id)
      )
      
      if next is not None:
        query = query.filter(Organism.id > next)
      elif prev is not None:
        query = (
          query.filter(Organism.id < prev)
          .order_by(Organism.id.desc())
        )
      
      organisms = query.limit(PAGINATION_LIMIT).all()
      
      if prev is not None:
        organisms.reverse()
      
      return organisms
    
    finally:
      session.close()

  def get_organism_by_id(self, id: str):
    session = self.db.get_session()
    
    try:
      organism = (
        session.query(Organism)
        .options(
          joinedload(Organism.genomes).joinedload(Genome.annotations),
          joinedload(Organism.genomes).joinedload(Genome.source),
          joinedload(Organism.genomes).joinedload(Genome.genome_files).joinedload(GenomeFile.file)
        )
        .filter(Organism.id == id)
        .first()
      )
      
      if organism is None:
        raise EntityNotFoundException("Organism not found")
      
      return organism
    
    finally:
      session.close()

  def create_organism(self, name: str, tax_id: str, species_name: str, metadata: dict = None):
    session = self.db.get_session()

    try:
      organism = Organism(
        id=str(uuid.uuid4()),
        name=name,
        tax_id=tax_id,
        species_name=species_name,
        organism_metadata=metadata,
        created_at=datetime.utcnow()
      )

      session.add(organism)
      session.commit()
      session.refresh(organism)

      return organism

    finally:
      session.close()
