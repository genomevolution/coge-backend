from repository.biosample import BiosampleRepository
from model.biosample import Biosample

class BiosampleService:
  def __init__(self, biosampleRepository: BiosampleRepository):
    self.biosampleRepository = biosampleRepository

  def getBiosamplesList(self, next: str, prev: str) -> list[Biosample]:
    return self.biosampleRepository.getBiosamplesList(next, prev)
  
  def getBiosample(self, id:str):
    return self.biosampleRepository.getBiosample(id)
