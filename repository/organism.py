from repository.db import DB
from model.exceptions.entity_not_found import EntityNotFoundException
from model.dto.paginable import PAGINATION_LIMIT
from model import Annotation, AnnotationFile, Organism, Genome, GenomeFile
from sqlalchemy import and_, desc, func, or_
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
        .order_by(desc(Organism.created_at), desc(Organism.id))
      )
      
      if next is not None:
        cursor = self._get_cursor_organism(session, next)
        query = query.filter(
          or_(
            Organism.created_at < cursor.created_at,
            and_(Organism.created_at == cursor.created_at, Organism.id < cursor.id)
          )
        )
      elif prev is not None:
        cursor = self._get_cursor_organism(session, prev)
        query = (
          query.filter(
            or_(
              Organism.created_at > cursor.created_at,
              and_(Organism.created_at == cursor.created_at, Organism.id > cursor.id)
            )
          )
          .order_by(Organism.created_at, Organism.id)
        )
      
      organisms = query.limit(PAGINATION_LIMIT).all()
      
      if prev is not None:
        organisms.reverse()
      
      return organisms
    
    finally:
      session.close()

  def _get_cursor_organism(self, session, organism_id: str):
    organism = session.query(Organism).filter(Organism.id == organism_id).first()

    if organism is None:
      raise EntityNotFoundException("Organism not found")

    return organism

  def get_organism_by_id(self, id: str):
    session = self.db.get_session()
    
    try:
      organism = (
        session.query(Organism)
        .options(
          joinedload(Organism.genomes).joinedload(Genome.annotations),
          joinedload(Organism.genomes)
            .joinedload(Genome.annotations)
            .joinedload(Annotation.annotation_files)
            .joinedload(AnnotationFile.file),
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

  def find_organism_by_identity(self, name: str, tax_id: str, species_name: str):
    session = self.db.get_session()

    try:
      return (
        session.query(Organism)
        .filter(
          Organism.tax_id == tax_id,
          func.lower(Organism.name) == name.lower(),
          func.lower(Organism.species_name) == species_name.lower()
        )
        .first()
      )

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
