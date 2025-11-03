from repository.genome import GenomeRepository
from model.dto.file_upload_result import FileUploadResult
from model.dto.paginated_response import PaginatedResponse
from service.genome_uploader_service import GenomeUploaderService
from fastapi import UploadFile

class GenomeService:
  def __init__(self, genome_repository: GenomeRepository, genome_uploader_service: GenomeUploaderService):
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
    return self.genomeUploaderService.upload_genome_file(organism_id, genome_id, file)
