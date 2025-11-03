from repository.genome import GenomeRepository
from model.file_upload_result import FileUploadResult
from model.paginated_response import PaginatedResponse
from service.genomeUploaderService import GenomeUploaderService
from fastapi import UploadFile

class GenomeService:
  def __init__(self, genomeRepository: GenomeRepository, genomeUploaderService: GenomeUploaderService):
    self.genomeRepository = genomeRepository
    self.genomeUploaderService = genomeUploaderService

  def getGenomes(self, prev: str, next: str):
    genomes = self.genomeRepository.getGenomes(prev, next)
    return PaginatedResponse(genomes, prev, next, {
      "include_organism": True,
      "include_annotations": True,
      "include_files": True,
      "include_source": True
    })
  
  def getGenomeById(self, id: str) -> dict:
    genome = self.genomeRepository.getGenomeById(id)
    
    return genome.to_dict(
      include_organism=True,
      include_annotations=True,
      include_files=True,
      include_source=True
    )
  
  def uploadGenomeFile(self, organism_id: str, genome_id: str, file: UploadFile) -> FileUploadResult:
    return self.genomeUploaderService.uploadGenomeFile(organism_id, genome_id, file)
