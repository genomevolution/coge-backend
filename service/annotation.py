from fastapi import UploadFile
from repository.annotation import AnnotationRepository
from model.dto.file_upload_result import FileUploadResult
from typing import Protocol

from service.request_validation import validate_required_fields


ANNOTATION_NAME_FIELD = "name"
ANNOTATION_DESCRIPTION_FIELD = "description"
ANNOTATION_PUBLIC_FIELD = "public"
ANNOTATION_PRIMARY_FIELD = "primaryAnnotation"
ANNOTATION_REQUIRED_FIELDS = (
  ANNOTATION_NAME_FIELD,
  ANNOTATION_DESCRIPTION_FIELD
)
ANNOTATION_DEFAULT_PUBLIC = True
ANNOTATION_DEFAULT_PRIMARY = False
ANNOTATION_SERIALIZATION_OPTIONS = {"include_files": True}


class AnnotationUploader(Protocol):
  def upload_annotation_file(
    self,
    genome_id: str,
    annotation_id: str,
    file: UploadFile
  ) -> FileUploadResult:
    ...


class AnnotationService:
  def __init__(
    self,
    annotation_repository: AnnotationRepository,
    annotation_uploader_service: AnnotationUploader
  ):
    self.annotation_repository = annotation_repository
    self.annotation_uploader_service = annotation_uploader_service
  
  def upload_annotation_file(self, genome_id: str, annotation_id: str, file: UploadFile) -> FileUploadResult:
    return self.annotation_uploader_service.upload_annotation_file(
      genome_id,
      annotation_id,
      file
    )

  def create_annotation(self, genome_id: str, data: dict) -> dict:
    self._validate_create_payload(data)

    annotation = self.annotation_repository.create_annotation(
      genome_id=genome_id,
      name=data[ANNOTATION_NAME_FIELD].strip(),
      description=data[ANNOTATION_DESCRIPTION_FIELD].strip(),
      public=bool(data.get(ANNOTATION_PUBLIC_FIELD, ANNOTATION_DEFAULT_PUBLIC)),
      primary_annotation=bool(
        data.get(ANNOTATION_PRIMARY_FIELD, ANNOTATION_DEFAULT_PRIMARY)
      )
    )

    return annotation.to_dict(**ANNOTATION_SERIALIZATION_OPTIONS)

  def _validate_create_payload(self, data: dict):
    validate_required_fields(data, ANNOTATION_REQUIRED_FIELDS)
