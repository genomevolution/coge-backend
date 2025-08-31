from model.paginationMetadata import PaginationMetadata
from model.paginable import Paginable

class PaginatedResponse:
  def __init__(self, data: list[Paginable]):
    self.data = data
    if data is not None and len(data) > 0:
      self.metadata = PaginationMetadata(data[0].getId(), data[-1].getId())
