from repository.db import DB
from model.biosample import Biosample
from model.exceptions.entityNotFoundException import EntityNotFoundException
from model.paginable import PAGINATION_LIMIT

class BiosampleRepository:
  def __init__(self, db: DB):
    self.db = db

  def getBiosamplesList(self, next: str, prev: str) -> list[Biosample]:
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
    # BIOSAMPLE
    # |0:id|1:name|2:user_fk|3:tax_id|4:metadata|5:created_at|6:species_name
    return [
      Biosample(
        r[0], # id
        r[1], # name
        r[3], # tax id
        r[4], # meadata
        r[5], # created at
        r[6]) # species name
      for r in rows]

  def getBiosample(self, id:str) -> Biosample:
    rows = self.db.fetchTuplesWithPlaceholders(
      "SELECT * FROM biosample WHERE id = %s;",
      (id,))
    # BIOSAMPLE
    # |0:id|1:name|2:user_fk|3:tax_id|4:metadata|5:created_at|6:species_name
    if len(rows) < 1:
      raise EntityNotFoundException("Biosample not found")
    r = rows[0]
    return Biosample(
      r[0], # id
      r[1], # name
      r[3], # tax id
      r[4], # meadata
      r[5], # created at
      r[6]) # species name
  
  def searchBiosample(self, expression: str):
    pass
