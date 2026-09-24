from fastapi import UploadFile

from model.dto.file_upload_result import FileUploadResult
from model.exceptions.entity_not_found import EntityNotFoundException
from model.exceptions.file_upload import FileUploadException
from model.exceptions.file_url_generation import FileUrlGenerationException
from model.exceptions.invalid_file_type import InvalidFileTypeException
from repository.annotation import AnnotationRepository
from repository.file import FileRepository
from service.minio_service import MinIOService


ANNOTATION_ALLOWED_EXTENSIONS = (".gff3", ".gff3.gz")
ANNOTATION_CONTENT_TYPE = "text/plain"
ANNOTATION_FILE_TYPE = "GFF3"
ANNOTATION_UPLOAD_RESULT_TYPE = "annotation"
FILE_UPLOAD_SUCCESS_MESSAGE = "File uploaded successfully"
ANNOTATION_LINK_FAILURE_MESSAGE = "Failed to create annotation file link in database"
INVALID_ANNOTATION_FILENAME_TYPE = "annotation files with valid filename"


class AnnotationUploaderService:
  def __init__(
    self,
    minio_service: MinIOService,
    file_repository: FileRepository,
    annotation_repository: AnnotationRepository
  ):
    self.minio_service = minio_service
    self.file_repository = file_repository
    self.annotation_repository = annotation_repository

  def _validate_file_extension(self, filename: str) -> None:
    if not filename:
      raise InvalidFileTypeException("", [INVALID_ANNOTATION_FILENAME_TYPE])

    normalized_filename = filename.lower()
    if not any(
      normalized_filename.endswith(extension)
      for extension in ANNOTATION_ALLOWED_EXTENSIONS
    ):
      raise InvalidFileTypeException(filename, list(ANNOTATION_ALLOWED_EXTENSIONS))

  def _upload_annotation_file(
    self,
    genome_id: str,
    annotation_id: str,
    file: UploadFile
  ) -> FileUploadResult:
    self.annotation_repository.get_annotation_by_id(annotation_id)

    file_path = self.minio_service.generate_annotation_file_path(
      annotation_id,
      file.filename
    )
    file_data = file.file.read()
    file_size = len(file_data)
    file.file.seek(0)
    content_type = file.content_type or ANNOTATION_CONTENT_TYPE

    self.minio_service.upload_file(
      file_data=file.file,
      file_name=file_path,
      content_type=content_type,
      file_size=file_size
    )

    file_metadata = {
      "original_filename": file.filename,
      "file_size": file_size,
      "content_type": content_type,
      "genome_id": genome_id,
      "annotation_id": annotation_id
    }
    file_record = self.file_repository.create_file(file_path, file_metadata)

    annotation_file_link = self.file_repository.create_annotation_file_link(
      file_record.id,
      annotation_id,
      ANNOTATION_FILE_TYPE
    )
    if not annotation_file_link:
      raise FileUploadException(file.filename, ANNOTATION_LINK_FAILURE_MESSAGE)

    return FileUploadResult(
      message=FILE_UPLOAD_SUCCESS_MESSAGE,
      file_path=file_path,
      file_url=self.minio_service.get_file_url(file_path),
      file_type=ANNOTATION_UPLOAD_RESULT_TYPE
    )

  def upload_annotation_file(
    self,
    genome_id: str,
    annotation_id: str,
    file: UploadFile
  ) -> FileUploadResult:
    self._validate_file_extension(file.filename)

    try:
      return self._upload_annotation_file(genome_id, annotation_id, file)
    except (
      FileUploadException,
      FileUrlGenerationException,
      EntityNotFoundException
    ):
      raise
    except Exception as error:
      raise FileUploadException(file.filename, str(error)) from error
