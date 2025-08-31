from repository.db import DB
from model.biosample import Biosample
from model.exceptions.entityNotFoundException import EntityNotFoundException

class BiosampleRepository:
  def __init__(self, db: DB):
    self.db = db

  def getBiosamplesList(self) -> list[Biosample]:
    rows = self.db.fetchTuples("SELECT * FROM biosample;")
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
