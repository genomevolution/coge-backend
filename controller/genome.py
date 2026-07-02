from typing import Optional
from service.genome import GenomeService
from service.minio_service import MinIOService
from service.genome_processing_service import GenomeProcessingService
from model.dto.file_upload_result import FileUploadResult
from model.exceptions.entity_not_found import EntityNotFoundException
from model.exceptions.bucket_cannot_be_created import BucketCannotBeCreatedException
from model.exceptions.file_upload import FileUploadException
from model.exceptions.file_not_found import FileNotFoundException
from model.exceptions.file_download import FileDownloadException
from model.exceptions.invalid_file_type import InvalidFileTypeException
from model.exceptions.file_url_generation import FileUrlGenerationException
from fastapi import HTTPException, UploadFile, File

class GenomeController:
  def __init__(
    self, 
    genome_service: GenomeService, 
    minio_service: MinIOService,
    genome_processing_service: Optional[GenomeProcessingService] = None
  ):
    self.genome_service = genome_service
    self.minio_service = minio_service
    self.genome_processing_service = genome_processing_service

  def get_genomes(self, prev: str, next: str):
    if next is not None and prev is not None:
      raise HTTPException(status_code=400, detail="Only send previous or next")
    return self.genome_service.get_genomes(prev, next)

  def get_genome_by_id(self, id: str):
    try:
      return self.genome_service.get_genome_by_id(id)
    except EntityNotFoundException:
      raise HTTPException(status_code=404, detail="Genome not found")
    except Exception as e:
      raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

  def create_genome(self, organismId: str, data: dict):
    try:
      return self.genome_service.create_genome(organismId, data)
    except ValueError as e:
      raise HTTPException(status_code=400, detail=str(e))
    except EntityNotFoundException as e:
      raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
      raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

  def upload_genome_file(self, organismId: str, genomeId: str, file: UploadFile = File(...)):
    try:
      result = self.genome_service.upload_genome_file(organismId, genomeId, file)
      
      execution_id = None
      processing_status = None
      
      if file.filename.endswith(('.fa', '.fasta', '.fna')) and self.genome_processing_service:
        try:
          execution_id = self.genome_processing_service.start_genome_indexing(
            organism_id=organismId,
            genome_id=genomeId,
            fasta_minio_path=result.file_path,
            profile="standard"
          )
          processing_status = "RUNNING"
        except Exception as processing_error:
          processing_status = "FAILED"
          execution_id = None
      
      return {
        "message": result.message,
        "filePath": result.file_path,
        "fileUrl": result.file_url,
        "fileType": result.file_type,
        "processingExecutionId": execution_id,
        "processingStatus": processing_status
      }
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

  def download_file(self, filePath: str):
    try:
      return self.minio_service.download_file(filePath)
    except FileNotFoundException as e:
      raise HTTPException(status_code=404, detail=str(e))
    except FileDownloadException as e:
      raise HTTPException(status_code=500, detail=f"Download failed: {str(e)}")
    except Exception as e:
      raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")
  
  def get_processing_execution_status(self, execution_id: str):
    try:
      if not self.genome_processing_service:
        raise HTTPException(status_code=503, detail="Processing service not available")
      
      status = self.genome_processing_service.get_execution_status(execution_id)
      if status.get("status") == "NOT_FOUND":
        raise HTTPException(status_code=404, detail="Execution not found")
      
      return status
    except HTTPException:
      raise
    except Exception as e:
      raise HTTPException(status_code=500, detail=f"Failed to get execution status: {str(e)}")
  
  def finalize_processing_execution(self, execution_id: str):
    try:
      if not self.genome_processing_service:
        raise HTTPException(status_code=503, detail="Processing service not available")
      
      result = self.genome_processing_service.finalize_execution(execution_id)
      return result
    except ValueError as e:
      raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
      raise HTTPException(status_code=500, detail=f"Failed to finalize execution: {str(e)}")
  
  def cancel_processing_execution(self, execution_id: str):
    try:
      if not self.genome_processing_service:
        raise HTTPException(status_code=503, detail="Processing service not available")
      
      cancelled = self.genome_processing_service.cancel_execution(execution_id)
      if not cancelled:
        raise HTTPException(status_code=400, detail="Could not cancel execution")
      
      return {"message": "Execution cancelled successfully", "executionId": execution_id}
    except HTTPException:
      raise
    except Exception as e:
      raise HTTPException(status_code=500, detail=f"Failed to cancel execution: {str(e)}")
