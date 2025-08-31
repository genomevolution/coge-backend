from repository.genome import GenomeRepository
from repository.biosample import BiosampleRepository

class SearchService:
  def __init__(self, genomeRepository: GenomeRepository, biosampleRepository: BiosampleRepository):
    self.genomeRepository = genomeRepository
    self.biosampleRpository = biosampleRepository
