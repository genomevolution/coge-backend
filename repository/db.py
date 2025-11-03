from repository.dbConfig import DBConfig
import psycopg2
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

class DB:
  def __init__(self, dbConfig: DBConfig):
    if DBConfig is None:
      raise Exception("DB not configured")
    self.dbConfig = dbConfig
    self._engine = None
    self._session_factory = None

  def getSession(self) -> Session:
    if self._engine is None:
      config = self.dbConfig
      connection_string = f"postgresql://{config.user}:{config.password}@{config.host}:{config.port}/{config.name}"
      self._engine = create_engine(connection_string)
      self._session_factory = sessionmaker(bind=self._engine)
    
    return self._session_factory()
