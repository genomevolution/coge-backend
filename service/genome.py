from repository.genome import GenomeRepository
from model.genome import Genome
from model.fileUploadResult import FileUploadResult
from service.genomeUploaderService import GenomeUploaderService
from fastapi import UploadFile

class GenomeService:
  def __init__(self, genomeRepository: GenomeRepository, genomeUploaderService: GenomeUploaderService):
    self.genomeRepository = genomeRepository
    self.genomeUploaderService = genomeUploaderService

  def getGenomesList(self, prev: str, next: str) -> list[Genome]:
    return self.genomeRepository.getGenomesList(prev, next)
  
  def getGenomeById(self, id: str) -> dict:
    genome = self.genomeRepository.getGenomeById(id)
    
    result = genome.to_dict(
      include_organism=True,
      include_annotations=True,
      include_files=True
    )
    
    if genome.source:
      result["source"] = genome.source.to_dict()
    
    return result
  
  def upload_genome_file(self, organism_id: str, genome_id: str, file: UploadFile) -> FileUploadResult:
    return self.genomeUploaderService.upload_genome_file(organism_id, genome_id, file)
