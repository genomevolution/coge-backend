from model.genomeVisualizationFile import GenomeVisualizationFile
from model.paginable import Paginable
from model.organism import Organism

class Genome(Paginable):
  def __init__(
      self,
      id,
      organism = None,
      createdAt = None,
      name = None,
      description = None,
      public = None,
      accesionId = None,
      annotations = None,
      fileFaPath = None):
    self.id = id
    self.organism = organism
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
    self.createdAt = result[2] # created at
    self.name = result[3] # name
    self.description = result[4] # description
    self.public = result[5] # public
    self.accesionId = result[6] # accesion id
    if len(result) > 7:
      self.organism = Organism(result[7:])
      if len(result) > 22 and result[22]:
        self.filePath = result[22]
        self.genomeVisualizationFiles = GenomeVisualizationFile(result[22:])
    else :
      self.organism = None,
