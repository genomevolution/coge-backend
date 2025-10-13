from repository.organism import OrganismRepository
from model.organism import Organism

class OrganismService:
  def __init__(self, organismRepository: OrganismRepository):
    self.organismRepository = organismRepository

  def getOrganismsList(self, prev: str, next: str) -> list[Organism]:
    return self.organismRepository.getOrganismsList(prev, next)
  
  def getOrganism(self, id:str):
    return self.organismRepository.getOrganism(id)
