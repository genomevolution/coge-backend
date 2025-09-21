from repository.db import DB
from model.genome import Genome
from model.annotation import Annotation
from model.biosample import Biosample
from model.exceptions.entityNotFoundException import EntityNotFoundException
from model.paginable import PAGINATION_LIMIT

class GenomeRepository:
  def __init__(self, db: DB):
    self.db = db

  def getGenomesList(self, prev: str, next: str) -> list[Genome]:
    query = "SELECT * FROM genome JOIN biosample ON genome.biosample_fk = biosample.id LIMIT %s;"
    params = (PAGINATION_LIMIT,)
    if next is not None:
      query = "SELECT * FROM genome JOIN biosample ON genome.biosample_fk = biosample.id WHERE genome.id > %s LIMIT %s;"
      params = (next, PAGINATION_LIMIT)
    elif prev is not None:
      query = "SELECT * FROM genome JOIN biosample ON genome.biosample_fk = biosample.id WHERE genome.id < %s ORDER BY genome.id DESC LIMIT %s;"
      params = (prev, PAGINATION_LIMIT)
    rows = self.db.fetchTuplesWithPlaceholders(query, params)
    if prev is not None:
      rows.reverse()

    return [
      Genome(result = r)
      for r in rows]

  
  def getGenome(self, id:str) -> Genome:
    rows = self.db.fetchTuplesWithPlaceholders(
      "SELECT * FROM genome JOIN biosample ON genome.biosample_fk = biosample.id LEFT OUTER JOIN annotations ON genome.id = annotations.fk_genome WHERE genome.id = %s;",
      (id,))
    if len(rows) < 1:
      raise EntityNotFoundException("Genome not found")
    r0 = rows[0]
    genome = Genome(result = r0)

    annotations = [
      Annotation(result = r[15:])
      for r in rows]
    genome.annotations = annotations

    genomeFileRows = self.db.fetchTuplesWithPlaceholders(
      "SELECT files.path FROM genome_files JOIN files ON genome_files.file_fk = files.id WHERE genome_files.genome_fk = %s;",
      (id,))
    if len(genomeFileRows) > 0:
      fileRow = genomeFileRows[0]
      genome.filePath = fileRow[0]

    return genome

  def searchGenomes(self, expression: str):
    pass
