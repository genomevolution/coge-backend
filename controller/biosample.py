from service.biosample import BiosampleService
from model.paginatedResponse import PaginatedResponse
from model.exceptions.entityNotFoundException import EntityNotFoundException
from fastapi import HTTPException

class BiosampleController:
  def __init__(self, biosampleService: BiosampleService):
    self.biosampleService = biosampleService

  def getBiosamplesList(self, prev: str, next: str):
    if next is not None and prev is not None:
      raise HTTPException(status_code=400, detail="Only send previous or next")
    return PaginatedResponse(self.biosampleService.getBiosamplesList(prev, next), prev, next)
  
  def getBiosample(self, id:str):
    try:
      return self.biosampleService.getBiosample(id)
    except EntityNotFoundException:
      raise HTTPException(status_code=404, detail="Genome not found")
