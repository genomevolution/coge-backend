from fastapi import HTTPException
from service.source import SourceService


class SourceController:
  def __init__(self, source_service: SourceService):
    self.source_service = source_service

  def get_sources(self):
    try:
      return self.source_service.get_sources()
    except Exception as e:
      raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
