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
  
  def getGenome(self, id:str):
    return self.genomeRepository.getGenome(id)
  
  def upload_genome_file(self, organism_id: str, genome_id: str, file: UploadFile) -> FileUploadResult:
    return self.genomeUploaderService.upload_genome_file(organism_id, genome_id, file)
