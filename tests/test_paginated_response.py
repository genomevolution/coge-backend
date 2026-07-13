from model.dto.paginated_response import PaginatedResponse


class PaginableItem:
  def __init__(self, id: str):
    self.id = id

  def get_id(self):
    return self.id

  def to_dict(self):
    return {"id": self.id}


def test_first_page_uses_snake_case_get_id_for_next_metadata():
  response = PaginatedResponse(
    [PaginableItem("a"), PaginableItem("b"), PaginableItem("c")],
    prev=None,
    next=None
  )

  assert response.data == [{"id": "a"}, {"id": "b"}]
  assert response.metadata.previous is None
  assert response.metadata.next == "b"


def test_next_page_uses_snake_case_get_id_for_metadata():
  response = PaginatedResponse(
    [PaginableItem("b"), PaginableItem("c"), PaginableItem("d")],
    prev=None,
    next="b"
  )

  assert response.data == [{"id": "b"}, {"id": "c"}]
  assert response.metadata.previous == "b"
  assert response.metadata.next == "c"


def test_previous_page_uses_snake_case_get_id_for_metadata():
  response = PaginatedResponse(
    [PaginableItem("a"), PaginableItem("b"), PaginableItem("c")],
    prev="c",
    next=None
  )

  assert response.data == [{"id": "b"}, {"id": "c"}]
  assert response.metadata.previous == "b"
  assert response.metadata.next == "c"
