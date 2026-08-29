from repository.db import DB
from model import Source
from model.exceptions.entity_not_found import EntityNotFoundException


class SourceRepository:
  def __init__(self, db: DB):
    self.db = db

  def get_sources(self):
    session = self.db.get_session()

    try:
      return session.query(Source).order_by(Source.name).all()

    finally:
      session.close()

  def get_source_by_id(self, id: str):
    session = self.db.get_session()

    try:
      source = session.query(Source).filter(Source.id == id).first()
      if source is None:
        raise EntityNotFoundException("Source not found")

      return source

    finally:
      session.close()
