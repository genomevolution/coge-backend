from model.paginable import Paginable

class Biosample(Paginable):
  def __init__(self, id, name = None, taxId = None, metadata = None, createdAt = None, speciesName = None, genomes = None):
    self.id = id
    self.name = name
    self.taxId = taxId
    self.metadata = metadata
    self.createdAt = createdAt
    self.speciesName = speciesName
    self.genomes = genomes

  def __init__(self, result: tuple):
    # BIOSAMPLE
    # |0:id|1:name|2:user_fk|3:tax_id|4:metadata|5:created_at|6:species_name
      self.id = result[0] # id
      self.name = result[1] # name
      self.taxId = result[3] # tax id
      self.metadata = result[4] # meadata
      self.createdAt = result[5] # created at
      self.speciesName = result[6] # species name

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
