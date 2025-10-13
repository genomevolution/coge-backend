from repository.genome import GenomeRepository
from repository.organism import OrganismRepository

class SearchService:
  def __init__(self, genomeRepository: GenomeRepository, organismRepository: OrganismRepository):
    self.genomeRepository = genomeRepository
    self.organismRpository = organismRepository
