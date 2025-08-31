import os

class DBConfig:
  def __init__(self):
    dbUser = os.environ.get("DB_USER")
    if dbUser is None:
      raise Exception("DB user is not set")
    self.user = dbUser

    dbPassword = os.environ.get("DB_PASSWORD")
    if dbPassword is None:
      raise Exception("DB password is not set")
    self.password = dbPassword

    dbHost = os.environ.get("DB_HOST")
    if dbHost is None:
      raise Exception("DB host is not set")
    self.host = dbHost

    dbPort = os.environ.get("DB_PORT")
    if dbPort is None:
      raise Exception("DB post is not set")
    self.port = dbPort
    
    dbName = os.environ.get("DB_NAME")
    if dbName is None:
      raise Exception("DB name is not set")
    self.name = dbName
