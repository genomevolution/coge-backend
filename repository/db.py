from repository.dbConfig import DBConfig
import psycopg2

class DB:
  def __init__(self, dbConfig: DBConfig):
    if DBConfig is None:
      raise Exception("DB not configured")
    self.dbConfig = dbConfig

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