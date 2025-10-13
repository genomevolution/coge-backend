from service.organism import OrganismService
from model.paginatedResponse import PaginatedResponse
from model.exceptions.entityNotFoundException import EntityNotFoundException
from fastapi import HTTPException

class OrganismController:
  def __init__(self, organismService: OrganismService):
    self.organismService = organismService

  def getOrganismsList(self, prev: str, next: str):
    if next is not None and prev is not None:
      raise HTTPException(status_code=400, detail="Only send previous or next")
    return PaginatedResponse(self.organismService.getOrganismsList(prev, next), prev, next)
  
  def getOrganism(self, id:str):
    try:
      return self.organismService.getOrganism(id)
    except EntityNotFoundException:
      raise HTTPException(status_code=404, detail="Organism not found")
