from service.genome import GenomeService
from model.paginatedResponse import PaginatedResponse
from model.exceptions.entityNotFoundException import EntityNotFoundException
from fastapi import HTTPException

class GenomeController:
  def __init__(self, genomeService: GenomeService):
    self.genomeService = genomeService

  def getGenomesList(self, next, previous):
    if next is not None and previous is not None:
      raise HTTPException(status_code=400, detail="Only send next or previous")
    return PaginatedResponse(self.genomeService.getGenomesList())
  
  def getGenome(self, id:str):
    try:
      return self.genomeService.getGenome(id)
    except EntityNotFoundException:
      raise HTTPException(status_code=404, detail="Genome not found")
