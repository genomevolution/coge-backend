from service.genome import GenomeService
from service.minio_service import MinIOService
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
  def __init__(self, genome_service: GenomeService, minio_service: MinIOService):
    self.genome_service = genome_service
    self.minio_service = minio_service

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

  def upload_genome_file(self, organismId: str, genomeId: str, file: UploadFile = File(...)) -> FileUploadResult:
    try:
      return self.genome_service.upload_genome_file(organismId, genomeId, file)
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
