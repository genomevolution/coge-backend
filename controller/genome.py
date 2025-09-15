from service.genome import GenomeService
from service.minioService import MinIOService
from model.paginatedResponse import PaginatedResponse
from model.fileUploadResult import FileUploadResult
from model.exceptions.entityNotFoundException import EntityNotFoundException
from model.exceptions.bucketCannotBeCreatedException import BucketCannotBeCreatedException
from model.exceptions.fileUploadException import FileUploadException
from model.exceptions.fileNotFoundException import FileNotFoundException
from model.exceptions.fileDownloadException import FileDownloadException
from model.exceptions.fileDeleteException import FileDeleteException
from model.exceptions.invalidFileTypeException import InvalidFileTypeException
from model.exceptions.fileUrlGenerationException import FileUrlGenerationException
from fastapi import HTTPException, UploadFile, File, Form
from typing import Optional

class GenomeController:
  def __init__(self, genomeService: GenomeService, minioService: MinIOService):
    self.genomeService = genomeService
    self.minioService = minioService

  def getGenomesList(self, prev: str, next: str):
    if next is not None and prev is not None:
      raise HTTPException(status_code=400, detail="Only send previous or next")
    return PaginatedResponse(self.genomeService.getGenomesList(prev, next),  prev, next)
  
  def getGenome(self, id:str):
    try:
      return self.genomeService.getGenome(id)
    except EntityNotFoundException:
      raise HTTPException(status_code=404, detail="Genome not found")

  def uploadGenomeFile(self, biosampleId: str, file: UploadFile = File(...)) -> FileUploadResult:
    try:
      return self.genomeService.upload_genome_file(biosampleId, file)
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

  def uploadAnnotationFile(self, biosampleId: str, file: UploadFile = File(...)) -> FileUploadResult:
    try:
      return self.genomeService.upload_annotation_file(biosampleId, file)
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

  def downloadFile(self, filePath: str):
    try:
      return self.minioService.download_file(filePath)
    except FileNotFoundException as e:
      raise HTTPException(status_code=404, detail=str(e))
    except FileDownloadException as e:
      raise HTTPException(status_code=500, detail=f"Download failed: {str(e)}")
    except Exception as e:
      raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

  def deleteFile(self, filePath: str):
    try:
      self.minioService.delete_file(filePath)
      return {"message": "File deleted successfully", "file_path": filePath}
    except FileDeleteException as e:
      raise HTTPException(status_code=500, detail=f"Delete failed: {str(e)}")
    except Exception as e:
      raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")
