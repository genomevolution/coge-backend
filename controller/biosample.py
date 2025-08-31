from service.biosample import BiosampleService
from model.paginatedResponse import PaginatedResponse
from model.exceptions.entityNotFoundException import EntityNotFoundException
from fastapi import HTTPException

class BiosampleController:
  def __init__(self, biosampleService: BiosampleService):
    self.biosampleService = biosampleService

  def getBiosamplesList(self, next, previous):
    if next is not None and previous is not None:
      raise HTTPException(status_code=400, detail="Only send next or previous")
    return PaginatedResponse(self.biosampleService.getBiosamplesList())
  
  def getBiosample(self, id:str):
    try:
      return self.biosampleService.getBiosample(id)
    except EntityNotFoundException:
      raise HTTPException(status_code=404, detail="Genome not found")
