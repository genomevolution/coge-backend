from repository.organism import OrganismRepository
from model.organism import Organism

class OrganismService:
  def __init__(self, organismRepository: OrganismRepository):
    self.organismRepository = organismRepository

  def getOrganismsList(self, prev: str, next: str) -> list[Organism]:
    return self.organismRepository.getOrganismsList(prev, next)
  
  def getOrganismById(self, id: str) -> dict:
    organism = self.organismRepository.getOrganismById(id)
    
    result = organism.to_dict(include_genomes=True)
    
    return result