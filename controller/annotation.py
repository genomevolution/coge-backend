from service.annotation import AnnotationService
from model.dto.file_upload_result import FileUploadResult
from model.exceptions.entity_not_found import EntityNotFoundException
from model.exceptions.bucket_cannot_be_created import BucketCannotBeCreatedException
from model.exceptions.file_upload import FileUploadException
from model.exceptions.invalid_file_type import InvalidFileTypeException
from model.exceptions.file_url_generation import FileUrlGenerationException
from fastapi import HTTPException, UploadFile, File

class AnnotationController:
  def __init__(self, annotation_service: AnnotationService):
    self.annotation_service = annotation_service

  def upload_annotation_file(self, genomeId: str, annotationId: str, file: UploadFile = File(...)) -> FileUploadResult:
    try:
      return self.annotation_service.upload_annotation_file(genomeId, annotationId, file)
    except EntityNotFoundException as e:
      raise HTTPException(status_code=404, detail=f"Entity not found: {str(e)}")
    except BucketCannotBeCreatedException as e:
      raise HTTPException(status_code=500, detail=f"Storage service unavailable: {str(e)}")
    except FileUploadException as e:
      raise HTTPException(status_code=500, detail=f"File upload failed: {str(e)}")
    except InvalidFileTypeException as e:
      raise HTTPException(status_code=400, detail=str(e))
    except FileUrlGenerationException as e:
      raise HTTPException(status_code=500, detail=f"Failed to generate file URL: {str(e)}")
    except Exception as e:
      raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")
