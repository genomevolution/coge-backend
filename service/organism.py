from repository.organism import OrganismRepository
from model.dto.paginated_response import PaginatedResponse
from model.exceptions.duplicate_entity import DuplicateEntityException

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

  def create_organism(self, data: dict) -> dict:
    self._validate_create_payload(data)

    name = data.get("name").strip()
    tax_id = data.get("taxId").strip()
    species_name = data.get("speciesName").strip()
    self._validate_unique_identity(name, tax_id, species_name)

    organism = self.organismRepository.create_organism(
      name=name,
      tax_id=tax_id,
      species_name=species_name,
      metadata=data.get("metadata")
    )

    return organism.to_dict(include_genomes=True)

  def _validate_create_payload(self, data: dict):
    if data is None:
      raise ValueError("Request body is required")

    for field in ["name", "taxId", "speciesName"]:
      if not data.get(field) or not str(data.get(field)).strip():
        raise ValueError(f"{field} is required")

  def _validate_unique_identity(self, name: str, tax_id: str, species_name: str):
    existing_organism = self.organismRepository.find_organism_by_identity(
      name=name,
      tax_id=tax_id,
      species_name=species_name
    )

    if existing_organism is not None:
      raise DuplicateEntityException(
        "An organism with the same name, taxonomy ID, and species already exists"
      )
