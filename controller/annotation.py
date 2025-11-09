from service.annotation import AnnotationService
from service.annotation_processing_service import AnnotationProcessingService
from model.dto.file_upload_result import FileUploadResult
from model.exceptions.entity_not_found import EntityNotFoundException
from model.exceptions.bucket_cannot_be_created import BucketCannotBeCreatedException
from model.exceptions.file_upload import FileUploadException
from model.exceptions.invalid_file_type import InvalidFileTypeException
from model.exceptions.file_url_generation import FileUrlGenerationException
from fastapi import HTTPException, UploadFile, File

class AnnotationController:
  def __init__(
    self,
    annotation_service: AnnotationService,
    annotation_processing_service: AnnotationProcessingService
  ):
    self.annotation_service = annotation_service
    self.annotation_processing_service = annotation_processing_service

  def upload_annotation_file(self, organism_id: str, genome_id: str, annotation_id: str, file: UploadFile = File(...)):
    try:
      upload_result = self.annotation_service.upload_annotation_file(genome_id, annotation_id, file)
      
      execution_id = self.annotation_processing_service.start_annotation_processing(
        organism_id=organism_id,
        genome_id=genome_id,
        annotation_id=annotation_id,
        gff3_minio_path=upload_result.file_path,
        profile="standard"
      )
      
      return {
        "message": "Annotation file uploaded and processing started",
        "file_path": upload_result.file_path,
        "file_url": upload_result.file_url,
        "execution_id": execution_id,
        "status": "RUNNING"
      }
      
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
  
  def get_processing_execution_status(self, execution_id: str):
    try:
      return self.annotation_processing_service.get_execution_status(execution_id)
    except Exception as e:
      raise HTTPException(status_code=500, detail=f"Failed to get execution status: {str(e)}")
  
  def finalize_processing_execution(self, execution_id: str):
    try:
      return self.annotation_processing_service.finalize_execution(execution_id)
    except ValueError as e:
      raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
      raise HTTPException(status_code=500, detail=f"Failed to finalize execution: {str(e)}")
  
  def cancel_processing_execution(self, execution_id: str):
    try:
      cancelled = self.annotation_processing_service.cancel_execution(execution_id)
      if cancelled:
        return {"message": "Execution cancelled successfully", "execution_id": execution_id}
      return {"message": "Execution could not be cancelled", "execution_id": execution_id}
    except Exception as e:
      raise HTTPException(status_code=500, detail=f"Failed to cancel execution: {str(e)}")
