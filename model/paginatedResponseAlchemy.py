from model.paginationMetadata import PaginationMetadata
from model.paginable import PAGE_SIZE


class PaginatedResponseAlchemy:
    def __init__(self, data: list, prev: str, next: str, to_dict_params: dict = None):

        if to_dict_params is None:
            to_dict_params = {}
        
        if data is not None and len(data) > 0:
            if next is None and prev is None:
                if len(data) <= PAGE_SIZE:
                    self.data = [item.to_dict(**to_dict_params) for item in data]
                    self.metadata = PaginationMetadata(None, None)
                    return
                self.data = [item.to_dict(**to_dict_params) for item in data[0:PAGE_SIZE]]
                self.metadata = PaginationMetadata(None, data[-2].getId())
                return

            if next is not None:
                if len(data) <= PAGE_SIZE:
                    self.data = [item.to_dict(**to_dict_params) for item in data]
                    self.metadata = PaginationMetadata(data[0].getId(), None)
                    return
                self.data = [item.to_dict(**to_dict_params) for item in data[0:PAGE_SIZE]]
                self.metadata = PaginationMetadata(data[0].getId(), data[-2].getId())
                return

            if prev is not None:
                if len(data) <= PAGE_SIZE:
                    self.data = [item.to_dict(**to_dict_params) for item in data]
                    self.metadata = PaginationMetadata(None, data[-1].getId())
                    return
                self.data = [item.to_dict(**to_dict_params) for item in data[1:PAGE_SIZE + 1]]
                self.metadata = PaginationMetadata(data[1].getId(), data[-1].getId())
                return
        
        self.data = [item.to_dict(**to_dict_params) for item in data] if data else []

