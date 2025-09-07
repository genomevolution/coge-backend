from repository.biosample import BiosampleRepository
from model.biosample import Biosample

class BiosampleService:
  def __init__(self, biosampleRepository: BiosampleRepository):
    self.biosampleRepository = biosampleRepository

  def getBiosamplesList(self, prev: str, next: str) -> list[Biosample]:
    return self.biosampleRepository.getBiosamplesList(prev, next)
  
  def getBiosample(self, id:str):
    return self.biosampleRepository.getBiosample(id)
