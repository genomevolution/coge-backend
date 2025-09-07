from model.paginationMetadata import PaginationMetadata
from model.paginable import Paginable, PAGE_SIZE

class PaginatedResponse:
  def __init__(self, data: list[Paginable], prev: str, next: str):
    if data is not None and len(data) > 0:
      if next is None and prev is None:
        # First page/call
        if len(data) <= PAGE_SIZE:
          # No more pages
          self.data = data
          self.metadata = PaginationMetadata(None, None)
          return
        # There is more pages
        self.data = data[0:PAGE_SIZE]
        self.metadata = PaginationMetadata(None, data[-2].getId())
        return

      if next is not None:
        # There is a previous page
        if len(data) <= PAGE_SIZE:
          # No more following pages
          self.data = data
          self.metadata = PaginationMetadata(data[0].getId(), None)
          return
        # There is a following page
        self.data = data[0:PAGE_SIZE]
        self.metadata = PaginationMetadata(data[0].getId(), data[-2].getId())
        return

      if prev is not None:
        # There is a next page
        if len(data) <= PAGE_SIZE:
          # No more following pages
          self.data = data
          self.metadata = PaginationMetadata(None, data[-1].getId())
          return
        # There is a following page
        self.data = data[1:PAGE_SIZE + 1]
        self.metadata = PaginationMetadata(data[1].getId(), data[-1].getId())
        return
    self.data = data
