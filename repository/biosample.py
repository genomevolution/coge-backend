from repository.db import DB
from model.biosample import Biosample
from model.exceptions.entityNotFoundException import EntityNotFoundException
from model.paginable import PAGINATION_LIMIT
from model.genome import Genome

class BiosampleRepository:
  def __init__(self, db: DB):
    self.db = db

  def getBiosamplesList(self, prev: str, next: str) -> list[Biosample]:
    query = "SELECT * FROM biosample LIMIT %s;"
    params = (PAGINATION_LIMIT,)
    if next is not None:
      query = "SELECT * FROM biosample WHERE id > %s LIMIT %s;"
      params = (next, PAGINATION_LIMIT)
    elif prev is not None:
      query = "SELECT * FROM biosample WHERE id < %s ORDER BY id DESC LIMIT %s;"
      params = (prev, PAGINATION_LIMIT)
    rows = self.db.fetchTuplesWithPlaceholders(query, params)
    if prev is not None:
      rows.reverse()
    return [
      Biosample(result = r)
      for r in rows]

  def getBiosample(self, id:str) -> Biosample:
    rows = self.db.fetchTuplesWithPlaceholders(
      "SELECT * FROM biosample LEFT JOIN genome ON genome.biosample_fk = biosample.id WHERE biosample.id = %s;",
      (id,))
    if len(rows) < 1:
      raise EntityNotFoundException("Biosample not found")
    r = rows[0]
    biosample = Biosample(result = r)
    genomes = [
      Genome(result = r[7:])
      for r in rows]
    biosample.genomes = genomes
    return biosample
  
  def searchBiosample(self, expression: str):
    pass
