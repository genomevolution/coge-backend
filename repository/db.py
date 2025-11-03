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

  def fetchTuples(self, query: str) -> list[tuple]:
    config = self.dbConfig
    connection = psycopg2.connect(
      dbname=config.name,
      user=config.user,
      password=config.password,
      host=config.host,
      port=config.port)
    cursor = connection.cursor()

    cursor.execute(query)
    rows =  cursor.fetchall()
    cursor.close()
    connection.close()
    return rows
  
  def fetchTuplesWithPlaceholders(self, query: str, params: tuple) -> list[tuple]:
    config = self.dbConfig
    connection = psycopg2.connect(
      dbname=config.name,
      user=config.user,
      password=config.password,
      host=config.host,
      port=config.port)
    cursor = connection.cursor()

    cursor.execute(query, params)
    rows =  cursor.fetchall()
    cursor.close()
    connection.close()
    return rows
  
  def executeWithPlaceholders(self, query: str, params: tuple) -> None:
    """Execute a query with parameters (INSERT, UPDATE, DELETE)"""
    config = self.dbConfig
    connection = psycopg2.connect(
      dbname=config.name,
      user=config.user,
      password=config.password,
      host=config.host,
      port=config.port)
    cursor = connection.cursor()

    cursor.execute(query, params)
    connection.commit()
    cursor.close()
    connection.close()
  
  def getAlchemySession(self) -> Session:
    """Get a SQLAlchemy session for ORM operations"""
    if self._engine is None:
      config = self.dbConfig
      connection_string = f"postgresql://{config.user}:{config.password}@{config.host}:{config.port}/{config.name}"
      self._engine = create_engine(connection_string)
      self._session_factory = sessionmaker(bind=self._engine)
    
    return self._session_factory()