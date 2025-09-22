class AnnotationEntity:
    def __init__(self, id, createdAt = None, name = None, description = None, public = None, primaryAnnotation = None, filePath = None):
      self.id = id
      self.createdAt = createdAt
      self.name = name
      self.description = description
      self.public = public
      self.primaryAnnotation = primaryAnnotation
      self.filePath = filePath

    def __init__(self, result: tuple):
    # ANNOTATIONS
    # 0:id|1:fk_genome|2:created_at|3:name|4:description|5:public|6:primary_annotation
    # FILE
    # 7:annotation_file_path
      self.id = result[0] # id
      self.createdAt = result[2] # created_at
      self.name = result[3] # name
      self.description = result[4] # description
      self.public = result[5] # public
      self.primaryAnnotation = result[6] # primary_annotation
      self.filePath = None
      if len(result) > 7 and result[7]:
         self.filePath = result[7]

