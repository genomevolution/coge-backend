from collections.abc import Mapping, Sequence
from typing import Any


REQUEST_BODY_REQUIRED_MESSAGE = "Request body is required"
REQUIRED_FIELD_MESSAGE_TEMPLATE = "{field} is required"


def validate_required_fields(
  data: Mapping[str, Any] | None,
  required_fields: Sequence[str]
) -> None:
  if data is None:
    raise ValueError(REQUEST_BODY_REQUIRED_MESSAGE)

  for field in required_fields:
    value = data.get(field)
    if value is None or not str(value).strip():
      raise ValueError(REQUIRED_FIELD_MESSAGE_TEMPLATE.format(field=field))
