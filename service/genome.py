from repository.genome import GenomeRepository
from model.genome import Genome
from model.fileUploadResult import FileUploadResult
from service.genomeUploaderService import GenomeUploaderService
from service.annotationUploaderService import AnnotationUploaderService
from fastapi import UploadFile

class GenomeService:
  def __init__(self, genomeRepository: GenomeRepository, genomeUploaderService: GenomeUploaderService, annotationUploaderService: AnnotationUploaderService):
    self.genomeRepository = genomeRepository
    self.genomeUploaderService = genomeUploaderService
    self.annotationUploaderService = annotationUploaderService

  def getGenomesList(self, prev: str, next: str) -> list[Genome]:
    return self.genomeRepository.getGenomesList(prev, next)
  
  def getGenome(self, id:str):
    return self.genomeRepository.getGenome(id)
  
  def upload_genome_file(self, biosample_id: str, genome_id: str, file: UploadFile) -> FileUploadResult:
    return self.genomeUploaderService.upload_genome_file(biosample_id, genome_id, file)
  
  def upload_annotation_file(self, biosample_id: str, genome_id: str, file: UploadFile) -> dict:
    return self.annotationUploaderService.upload_annotation_file(biosample_id, genome_id, file)
