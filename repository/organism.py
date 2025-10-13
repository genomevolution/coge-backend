from repository.db import DB
from model.organism import Organism
from model.exceptions.entityNotFoundException import EntityNotFoundException
from model.paginable import PAGINATION_LIMIT
from model.genome import Genome

class OrganismRepository:
  def __init__(self, db: DB):
    self.db = db

  def getOrganismsList(self, prev: str, next: str) -> list[Organism]:
    query = "SELECT * FROM organism LIMIT %s;"
    params = (PAGINATION_LIMIT,)
    if next is not None:
      query = "SELECT * FROM organism WHERE id > %s LIMIT %s;"
      params = (next, PAGINATION_LIMIT)
    elif prev is not None:
      query = "SELECT * FROM organism WHERE id < %s ORDER BY id DESC LIMIT %s;"
      params = (prev, PAGINATION_LIMIT)
    rows = self.db.fetchTuplesWithPlaceholders(query, params)
    if prev is not None:
      rows.reverse()
    return [
      Organism(result = r)
      for r in rows]

  def getOrganism(self, id:str) -> Organism:
    rows = self.db.fetchTuplesWithPlaceholders(
      "SELECT * FROM organism LEFT JOIN genome ON genome.organism_fk = organism.id WHERE organism.id = %s;",
      (id,))
    if len(rows) < 1:
      raise EntityNotFoundException("Organism not found")
    r = rows[0]
    organism = Organism(result = r)
    genomes = []
    for r in rows:
      genome_data = r[7:]
      if any(genome_data):
        genomes.append(Genome(result = genome_data))
    organism.genomes = genomes
    return organism
  
  def searchOrganism(self, expression: str):
    pass
