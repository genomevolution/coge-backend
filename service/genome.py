from repository.genome import GenomeRepository
from model.dto.file_upload_result import FileUploadResult
from model.dto.paginated_response import PaginatedResponse
from fastapi import UploadFile
from typing import Protocol

from service.request_validation import validate_required_fields


GENOME_NAME_FIELD = "name"
GENOME_DESCRIPTION_FIELD = "description"
GENOME_PUBLIC_FIELD = "public"
GENOME_ACCESSION_ID_FIELD = "accessionId"
GENOME_SOURCE_ID_FIELD = "sourceId"
GENOME_REQUIRED_FIELDS = (
  GENOME_NAME_FIELD,
  GENOME_DESCRIPTION_FIELD,
  GENOME_ACCESSION_ID_FIELD,
  GENOME_SOURCE_ID_FIELD
)
GENOME_DEFAULT_PUBLIC = True
GENOME_LIST_SERIALIZATION_OPTIONS = {
  "include_organism": True,
  "include_annotations": True,
  "include_files": True,
  "include_source": True
}
GENOME_CREATE_SERIALIZATION_OPTIONS = {
  "include_organism": False,
  "include_annotations": False,
  "include_files": False,
  "include_source": False
}


class GenomeUploader(Protocol):
  def upload_genome_file(self, organism_id: str, genome_id: str, file: UploadFile) -> FileUploadResult:
    ...

class GenomeService:
  def __init__(self, genome_repository: GenomeRepository, genome_uploader_service: GenomeUploader):
    self.genome_repository = genome_repository
    self.genome_uploader_service = genome_uploader_service

  def get_genomes(self, prev: str, next: str):
    genomes = self.genome_repository.get_genomes(prev, next)
    return PaginatedResponse(
      genomes,
      prev,
      next,
      GENOME_LIST_SERIALIZATION_OPTIONS
    )
  
  def get_genome_by_id(self, id: str) -> dict:
    genome = self.genome_repository.get_genome_by_id(id)
    
    return genome.to_dict(**GENOME_LIST_SERIALIZATION_OPTIONS)
  
  def upload_genome_file(self, organism_id: str, genome_id: str, file: UploadFile) -> FileUploadResult:
    return self.genome_uploader_service.upload_genome_file(organism_id, genome_id, file)

  def create_genome(self, organism_id: str, data: dict) -> dict:
    self._validate_create_payload(data)

    genome = self.genome_repository.create_genome(
      organism_id=organism_id,
      name=data[GENOME_NAME_FIELD].strip(),
      description=data[GENOME_DESCRIPTION_FIELD].strip(),
      public=bool(data.get(GENOME_PUBLIC_FIELD, GENOME_DEFAULT_PUBLIC)),
      accession_id=data[GENOME_ACCESSION_ID_FIELD].strip(),
      source_id=data[GENOME_SOURCE_ID_FIELD]
    )

    return genome.to_dict(**GENOME_CREATE_SERIALIZATION_OPTIONS)

  def _validate_create_payload(self, data: dict):
    validate_required_fields(data, GENOME_REQUIRED_FIELDS)
