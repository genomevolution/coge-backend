from model.paginable import Paginable
from model.biosample import Biosample

class Genome(Paginable):
  def __init__(self, id, biosample, prefix, createdAt, name, description, public, accesionId):
    self.id = id
    self.biosample = biosample
    self.prefix = prefix
    self.createdAt = createdAt
    self.name = name
    self.description = description
    self.public = public
    self.accesionId = accesionId
  
  def getId(self):
    return self.id
  
  def buildSampleGenome(uuid: str):
    return Genome(
      uuid,
      Biosample.buildSampleBiosample("Biosample"+uuid),
      "prefix",
      "createdAt",
      "name",
      "description",
      True,
      "accesionId")
