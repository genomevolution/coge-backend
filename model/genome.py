from model.genomeVisualizationFile import GenomeVisualizationFile
from model.paginable import Paginable
from model.organism import Organism

class Genome(Paginable):
  def __init__(
      self,
      id,
      organism = None,
      prefix = None,
      createdAt = None,
      name = None,
      description = None,
      public = None,
      accesionId = None,
      annotations = None,
      fileFaPath = None):
    self.id = id
    self.organism = organism
    self.prefix = prefix
    self.createdAt = createdAt
    self.name = name
    self.description = description
    self.public = public
    self.accesionId = accesionId
    self.annotations = annotations
    self.fileFaPath = fileFaPath
    self.genomeVisualizationFiles = None
  
  def getId(self):
    return self.id
  
  def __init__(self, result: tuple):
    self.id = result[0] # id
    self.prefix = result[2] # prefix
    self.createdAt = result[3] # created at
    self.name = result[4] # name
    self.description = result[5] # description
    self.public = result[6] # public
    self.accesionId = result[7] # accesion id
    if len(result) > 8:
      self.organism = Organism(result[8:])
      if len(result) > 23 and result[23]:
        self.filePath = result[23]
        self.genomeVisualizationFiles = GenomeVisualizationFile(result[23:])
    else :
      self.organism = None,
