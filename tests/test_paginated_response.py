from model.dto.paginated_response import PaginatedResponse
from model.dto.paginable import PAGE_SIZE


class PaginableItem:
  def __init__(self, id: str):
    self.id = id

  def get_id(self):
    return self.id

  def to_dict(self):
    return {"id": self.id}


def test_first_page_uses_snake_case_get_id_for_next_metadata():
  items = [PaginableItem(str(index)) for index in range(PAGE_SIZE + 1)]

  response = PaginatedResponse(
    items,
    prev=None,
    next=None
  )

  assert response.data == [{"id": str(index)} for index in range(PAGE_SIZE)]
  assert response.metadata.previous is None
  assert response.metadata.next == str(PAGE_SIZE - 1)


def test_next_page_uses_snake_case_get_id_for_metadata():
  items = [PaginableItem(str(index)) for index in range(PAGE_SIZE + 1)]

  response = PaginatedResponse(
    items,
    prev=None,
    next="0"
  )

  assert response.data == [{"id": str(index)} for index in range(PAGE_SIZE)]
  assert response.metadata.previous == "0"
  assert response.metadata.next == str(PAGE_SIZE - 1)


def test_previous_page_uses_snake_case_get_id_for_metadata():
  items = [PaginableItem(str(index)) for index in range(PAGE_SIZE + 1)]

  response = PaginatedResponse(
    items,
    prev=str(PAGE_SIZE),
    next=None
  )

  assert response.data == [{"id": str(index)} for index in range(1, PAGE_SIZE + 1)]
  assert response.metadata.previous == "1"
  assert response.metadata.next == str(PAGE_SIZE)
