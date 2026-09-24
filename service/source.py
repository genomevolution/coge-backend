from repository.source import SourceRepository


class SourceService:
  def __init__(self, source_repository: SourceRepository):
    self.source_repository = source_repository

  def get_sources(self):
    sources = self.source_repository.get_sources()
    return [source.to_dict() for source in sources]
