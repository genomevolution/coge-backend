from repository.db import DB
from model.annotationEntity import AnnotationEntity
from model.exceptions.entityNotFoundException import EntityNotFoundException

class AnnotationRepository:
  def __init__(self, db: DB):
    self.db = db

  def getAnnotation(self, id:str) -> AnnotationEntity:
    rows = self.db.fetchTuplesWithPlaceholders(
      "SELECT * FROM organism_data.annotations WHERE id = %s;",
      (id,))
    if len(rows) < 1:
      raise EntityNotFoundException("Annotation not found")
    r = rows[0]
    annotation = AnnotationEntity(result = r)

    annotationFileRows = self.db.fetchTuplesWithPlaceholders(
      "SELECT data_files.files.path FROM data_files.annotation_files JOIN data_files.files ON data_files.annotation_files.file_fk = data_files.files.id WHERE data_files.annotation_files.annotation_fk = %s;",
      (id,))
    if len(annotationFileRows) > 0:
      fileRow = annotationFileRows[0]
      annotation.filePath = fileRow[0]

    return annotation

