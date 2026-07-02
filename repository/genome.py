from repository.db import DB
from model.exceptions.entity_not_found import EntityNotFoundException
from model.dto.paginable import PAGINATION_LIMIT
from model import Genome, GenomeFile, Annotation, AnnotationFile, Organism, Source
from sqlalchemy.orm import joinedload
from datetime import datetime
import uuid

class GenomeRepository:
  def __init__(self, db: DB):
    self.db = db

  def get_genomes(self, prev: str, next: str) -> list:
    session = self.db.get_session()
    
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

  def create_genome(
    self,
    organism_id: str,
    name: str,
    description: str,
    public: bool,
    accession_id: str,
    source_id: str = None
  ):
    session = self.db.get_session()

    try:
      organism = session.query(Organism).filter(Organism.id == organism_id).first()
      if organism is None:
        raise EntityNotFoundException("Organism not found")

      if source_id:
        source = session.query(Source).filter(Source.id == source_id).first()
        if source is None:
          raise EntityNotFoundException("Source not found")

      genome = Genome(
        id=str(uuid.uuid4()),
        organism_fk=organism_id,
        created_at=datetime.utcnow(),
        name=name,
        description=description,
        public=public,
        accesion_id=accession_id,
        source_fk=source_id
      )

      session.add(genome)
      session.commit()
      session.refresh(genome)

      return genome

    finally:
      session.close()

  def get_genome_by_id(self, id: str):
    session = self.db.get_session()
    
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
    
