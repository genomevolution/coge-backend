from service.annotation import AnnotationService
from model.fileUploadResult import FileUploadResult
from model.exceptions.entityNotFoundException import EntityNotFoundException
from model.exceptions.bucketCannotBeCreatedException import BucketCannotBeCreatedException
from model.exceptions.fileUploadException import FileUploadException
from model.exceptions.invalidFileTypeException import InvalidFileTypeException
from model.exceptions.fileUrlGenerationException import FileUrlGenerationException
from fastapi import HTTPException, UploadFile, File

class AnnotationController:
  def __init__(self, annotationService: AnnotationService):
    self.annotationService = annotationService

  def uploadAnnotationFile(self, genomeId: str, annotationId: str, file: UploadFile = File(...)) -> FileUploadResult:
    try:
      return self.annotationService.upload_annotation_file(genomeId, annotationId, file)
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
