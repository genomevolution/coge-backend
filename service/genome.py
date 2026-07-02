from repository.genome import GenomeRepository
from model.dto.file_upload_result import FileUploadResult
from model.dto.paginated_response import PaginatedResponse
from fastapi import UploadFile
from typing import Protocol


class GenomeUploader(Protocol):
  def upload_genome_file(self, organism_id: str, genome_id: str, file: UploadFile) -> FileUploadResult:
    ...

class GenomeService:
  def __init__(self, genome_repository: GenomeRepository, genome_uploader_service: GenomeUploader):
    self.genome_repository = genome_repository
    self.genome_uploader_service = genome_uploader_service

  def get_genomes(self, prev: str, next: str):
    genomes = self.genome_repository.get_genomes(prev, next)
    return PaginatedResponse(genomes, prev, next, {
      "include_organism": True,
      "include_annotations": True,
      "include_files": True,
      "include_source": True
    })
  
  def get_genome_by_id(self, id: str) -> dict:
    genome = self.genome_repository.get_genome_by_id(id)
    
    return genome.to_dict(
      include_organism=True,
      include_annotations=True,
      include_files=True,
      include_source=True
    )
  
  def upload_genome_file(self, organism_id: str, genome_id: str, file: UploadFile) -> FileUploadResult:
    return self.genome_uploader_service.upload_genome_file(organism_id, genome_id, file)

  def create_genome(self, organism_id: str, data: dict) -> dict:
    self._validate_create_payload(data)

    genome = self.genome_repository.create_genome(
      organism_id=organism_id,
      name=data.get("name").strip(),
      description=data.get("description").strip(),
      public=bool(data.get("public", True)),
      accession_id=data.get("accessionId").strip(),
      source_id=data.get("sourceId")
    )

    return genome.to_dict(
      include_organism=False,
      include_annotations=False,
      include_files=False,
      include_source=False
    )

  def _validate_create_payload(self, data: dict):
    if data is None:
      raise ValueError("Request body is required")

    for field in ["name", "description", "accessionId", "sourceId"]:
      if not data.get(field) or not str(data.get(field)).strip():
        raise ValueError(f"{field} is required")
