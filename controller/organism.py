from service.organism import OrganismService
from model.exceptions.entityNotFoundException import EntityNotFoundException
from fastapi import HTTPException

class OrganismController:
  def __init__(self, organismService: OrganismService):
    self.organismService = organismService

  def getOrganisms(self, prev: str, next: str):
    if next is not None and prev is not None:
      raise HTTPException(status_code=400, detail="Only send previous or next")
    return self.organismService.getOrganisms(prev, next)
  
  def getOrganismById(self, id: str):
    try:
      return self.organismService.getOrganismById(id)
    except EntityNotFoundException:
      raise HTTPException(status_code=404, detail="Organism not found")
    except Exception as e:
      raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")