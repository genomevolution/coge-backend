from fastapi import UploadFile
from repository.file import FileRepository
from repository.annotation import AnnotationRepository
from model.exceptions.file_upload import FileUploadException
from model.exceptions.invalid_file_type import InvalidFileTypeException
from model.exceptions.file_url_generation import FileUrlGenerationException
from model.exceptions.entity_not_found import EntityNotFoundException
from model.dto.file_upload_result import FileUploadResult
from typing import BinaryIO, Protocol


class MinIOClient(Protocol):
  def upload_file(self, file_data: BinaryIO, file_name: str, content_type: str, file_size: int) -> str:
    ...

  def get_file_url(self, file_name: str, expires_in_seconds: int = 3600) -> str:
    ...

class AnnotationService:
  def __init__(self, minio_service: MinIOClient, file_repository: FileRepository, annotation_repository: AnnotationRepository):
    self.minio_service = minio_service
    self.file_repository = file_repository
    self.annotation_repository = annotation_repository
    self.allowed_extensions = ['.gff3', '.gff', '.gz']
    
  def _validate_file_extension(self, filename: str) -> None:
    if not filename:
      raise InvalidFileTypeException("", ["annotation files with valid filename"])
    
    file_extension = '.' + filename.split('.')[-1].lower()
    if file_extension not in self.allowed_extensions:
      raise InvalidFileTypeException(
        file_extension,
        self.allowed_extensions
      )
  
  def _upload_annotation_file(self, genome_id: str, annotation_id: str, file: UploadFile) -> FileUploadResult:
   
    self.annotation_repository.get_annotation_by_id(annotation_id)
    
    file_path = f"annotation/{annotation_id}/{file.filename}"
    file_data = file.file.read()
    file_size = len(file_data)
    file.file.seek(0)
    
    self.minio_service.upload_file(
      file_data=file.file,
      file_name=file_path,
      content_type=file.content_type or "text/plain",
      file_size=file_size
    )
    
    file_metadata = {
      "original_filename": file.filename,
      "file_size": file_size,
      "content_type": file.content_type or "text/plain",
      "genome_id": genome_id,
      "annotation_id": annotation_id
    }

    file_record = self.file_repository.create_file(file_path, file_metadata)
    
    annotation_file_link = self.file_repository.create_annotation_file_link(
      file_record.id,
      annotation_id,
      "GFF3"
    )
    
    if not annotation_file_link:
      raise FileUploadException(file.filename, "Failed to create annotation file link in database")
    
    file_url = self.minio_service.get_file_url(file_path)
    
    return FileUploadResult(
      message="File uploaded successfully",
      file_path=file_path,
      file_url=file_url,
      file_type="annotation"
    )
  
  def upload_annotation_file(self, genome_id: str, annotation_id: str, file: UploadFile) -> FileUploadResult:
    self._validate_file_extension(file.filename)
    try:
      return self._upload_annotation_file(genome_id, annotation_id, file)
    except (FileUploadException, FileUrlGenerationException, EntityNotFoundException) as e:
      raise e
    except Exception as e:
      raise FileUploadException(file.filename, str(e))

  def create_annotation(self, genome_id: str, data: dict) -> dict:
    self._validate_create_payload(data)

    annotation = self.annotation_repository.create_annotation(
      genome_id=genome_id,
      name=data.get("name").strip(),
      description=data.get("description").strip(),
      public=bool(data.get("public", True)),
      primary_annotation=bool(data.get("primaryAnnotation", False))
    )

    return annotation.to_dict(include_files=True)

  def _validate_create_payload(self, data: dict):
    if data is None:
      raise ValueError("Request body is required")

    for field in ["name", "description"]:
      if not data.get(field) or not str(data.get(field)).strip():
        raise ValueError(f"{field} is required")
