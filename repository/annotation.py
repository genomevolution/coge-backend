from repository.db import DB
from model.annotationEntity import AnnotationEntity
from model.exceptions.entityNotFoundException import EntityNotFoundException

class AnnotationRepository:
  def __init__(self, db: DB):
    self.db = db

  def getAnnotation(self, id:str) -> AnnotationEntity:
    rows = self.db.fetchTuplesWithPlaceholders(
      "SELECT * FROM annotations WHERE id = %s;",
      (id,))
    if len(rows) < 1:
      raise EntityNotFoundException("Annotation not found")
    r = rows[0]
    annotation = AnnotationEntity(result = r)

    annotationFileRows = self.db.fetchTuplesWithPlaceholders(
      "SELECT files.path FROM annotation_files JOIN files ON annotation_files.file_fk = files.id WHERE annotation_files.annotation_fk = %s;",
      (id,))
    if len(annotationFileRows) > 0:
      fileRow = annotationFileRows[0]
      annotation.filePath = fileRow[0]

    return annotation

