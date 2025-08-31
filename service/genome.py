from repository.genome import GenomeRepository
from model.genome import Genome

class GenomeService:
  def __init__(self, genomeRepository: GenomeRepository):
    self.genomeRepository = genomeRepository

  def getGenomesList(self) -> list[Genome]:
    return self.genomeRepository.getGenomesList()
  
  def getGenome(self, id:str):
    return self.genomeRepository.getGenome(id)
