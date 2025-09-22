from model.paginable import Paginable
from model.biosample import Biosample

class Genome(Paginable):
  def __init__(
      self,
      id,
      biosample = None,
      prefix = None,
      createdAt = None,
      name = None,
      description = None,
      public = None,
      accesionId = None,
      annotations = None,
      filePath = None):
    self.id = id
    self.biosample = biosample
    self.prefix = prefix
    self.createdAt = createdAt
    self.name = name
    self.description = description
    self.public = public
    self.accesionId = accesionId
    self.annotations = annotations
    self.filePath = filePath
  
  def getId(self):
    return self.id
  
  def __init__(self, result: tuple):
    # GENOME
    # 0:id|1:biosample_fk|2:prefix|3:created_at|4:name|5:description|6:public|7:accesion_id
    # BIOSAMPLE
    # |8:id|9:name|10:user_fk|11:tax_id|12:metadata|13:created_at|14:species_name
    # ANNOTATIONS
    # |15:id|16:fk_genome|17:created_at|18:name|19:description|20:public|21:primary_annotation
    # FILES
    # 22:annotation_file_path|23:genome_file_path
    self.id = result[0] # id
    self.prefix = result[2] # prefix
    self.createdAt = result[3] # created at
    self.name = result[4] # name
    self.description = result[5] # description
    self.public = result[6] # public
    self.accesionId = result[7] # accesion id
    self.filePath = None
    if len(result) > 8:
      self.biosample = Biosample(result[8:])
      if len(result) > 23 and result[23]:
        self.filePath = result[23]
    else :
      self.biosample = None,
