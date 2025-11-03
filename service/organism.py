from repository.organism import OrganismRepository
from model.paginated_response import PaginatedResponse

class OrganismService:
  def __init__(self, organismRepository: OrganismRepository):
    self.organismRepository = organismRepository

  def getOrganisms(self, prev: str, next: str):
    organisms = self.organismRepository.getOrganisms(prev, next)
    return PaginatedResponse(organisms, prev, next, {"include_genomes": True})
  
  def getOrganismById(self, id: str) -> dict:
    organism = self.organismRepository.getOrganismById(id)
    
    result = organism.to_dict(include_genomes=True)
    
    return result