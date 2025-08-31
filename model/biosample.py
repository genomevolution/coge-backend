from model.paginable import Paginable

class Biosample(Paginable):
  def __init__(self, id, name, taxId, metadata, createdAt, speciesName):
    self.id = id
    self.name = name
    self.taxId = taxId
    self.metadata = metadata
    self.createdAt = createdAt
    self.speciesName = speciesName

  def getId(self):
    return self.id
  
  def buildSampleBiosample(uuid: str):
    return Biosample(
      uuid,
      "name",
      "taxId",
      "metadataJSON",
      "createdAt",
      "speciesName")
