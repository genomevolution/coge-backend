from repository.organism import OrganismRepository
from model.dto.paginated_response import PaginatedResponse
from model.exceptions.duplicate_entity import DuplicateEntityException
from service.request_validation import validate_required_fields


ORGANISM_NAME_FIELD = "name"
ORGANISM_TAXONOMY_ID_FIELD = "taxId"
ORGANISM_SPECIES_NAME_FIELD = "speciesName"
ORGANISM_METADATA_FIELD = "metadata"
ORGANISM_REQUIRED_FIELDS = (
  ORGANISM_NAME_FIELD,
  ORGANISM_TAXONOMY_ID_FIELD,
  ORGANISM_SPECIES_NAME_FIELD
)
ORGANISM_SERIALIZATION_OPTIONS = {"include_genomes": True}
DUPLICATE_ORGANISM_MESSAGE = (
  "An organism with the same name, taxonomy ID, and species already exists"
)


class OrganismService:
  def __init__(self, organismRepository: OrganismRepository):
    self.organismRepository = organismRepository

  def get_organisms(self, prev: str, next: str):
    organisms = self.organismRepository.get_organisms(prev, next)
    return PaginatedResponse(
      organisms,
      prev,
      next,
      ORGANISM_SERIALIZATION_OPTIONS
    )
  
  def get_organism_by_id(self, id: str) -> dict:
    organism = self.organismRepository.get_organism_by_id(id)
    
    result = organism.to_dict(**ORGANISM_SERIALIZATION_OPTIONS)
    
    return result

  def create_organism(self, data: dict) -> dict:
    self._validate_create_payload(data)

    name = data[ORGANISM_NAME_FIELD].strip()
    tax_id = data[ORGANISM_TAXONOMY_ID_FIELD].strip()
    species_name = data[ORGANISM_SPECIES_NAME_FIELD].strip()
    self._validate_unique_identity(name, tax_id, species_name)

    organism = self.organismRepository.create_organism(
      name=name,
      tax_id=tax_id,
      species_name=species_name,
      metadata=data.get(ORGANISM_METADATA_FIELD)
    )

    return organism.to_dict(**ORGANISM_SERIALIZATION_OPTIONS)

  def _validate_create_payload(self, data: dict):
    validate_required_fields(data, ORGANISM_REQUIRED_FIELDS)

  def _validate_unique_identity(self, name: str, tax_id: str, species_name: str):
    existing_organism = self.organismRepository.find_organism_by_identity(
      name=name,
      tax_id=tax_id,
      species_name=species_name
    )

    if existing_organism is not None:
      raise DuplicateEntityException(DUPLICATE_ORGANISM_MESSAGE)
