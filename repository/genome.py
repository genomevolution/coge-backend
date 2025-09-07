from repository.db import DB
from model.genome import Genome
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

    # GENOME
    # 0:id|1:biosample_fk|2:prefix|3:created_at|4:name|5:description|6:public|7:accesion_id
    # BIOSAMPLE
    # |8:id|9:name|10:user_fk|11:tax_id|12:metadata|13:created_at|14:species_name
    return [
      Genome(
        r[0], # id
        Biosample(
          r[8], # id
          r[9], # name
          r[11], # tax id
          r[12], # metadata
          r[13], # created at
          r[14]), # species name
        r[2], # prefix
        r[3], # created at
        r[4], # name
        r[5], # description
        r[6], # public
        r[7]) # accesion id
      for r in rows]

  
  def getGenome(self, id:str) -> Genome:
    rows = self.db.fetchTuplesWithPlaceholders(
      "SELECT * FROM genome JOIN biosample ON genome.biosample_fk = biosample.id WHERE genome.id = %s;",
      (id,))
    # GENOME
    # 0:id|1:biosample_fk|2:prefix|3:created_at|4:name|5:description|6:public|7:accesion_id
    # BIOSAMPLE
    # |8:id|9:name|10:user_fk|11:tax_id|12:metadata|13:created_at|14:species_name
    if len(rows) < 1:
      raise EntityNotFoundException("Genome not found")
    r = rows[0]
    return Genome(
      r[0], # id
      Biosample(
        r[8], # id
        r[9], # name
        r[11], # tax id
        r[12], # metadata
        r[13], # created at
        r[14]), # species name
      r[2], # prefix
      r[3], # created at
      r[4], # name
      r[5], # description
      r[6], # public
      r[7]) # accesion id

  def searchGenomes(self, expression: str):
    pass
