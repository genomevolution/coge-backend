from repository.organism import OrganismRepository
from model.dto.paginated_response import PaginatedResponse

class OrganismService:
  def __init__(self, organismRepository: OrganismRepository):
    self.organismRepository = organismRepository

  def get_organisms(self, prev: str, next: str):
    organisms = self.organismRepository.get_organisms(prev, next)
    return PaginatedResponse(organisms, prev, next, {"include_genomes": True})
  
  def get_organism_by_id(self, id: str) -> dict:
    organism = self.organismRepository.get_organism_by_id(id)
    
    result = organism.to_dict(include_genomes=True)
    
    return result