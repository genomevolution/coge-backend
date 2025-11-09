import os

class DBConfig:
  def __init__(self):
    db_user = os.environ.get("DB_USER")
    if db_user is None:
      raise Exception("DB user is not set")
    self.user = db_user

    db_password = os.environ.get("DB_PASSWORD")
    if db_password is None:
      raise Exception("DB password is not set")
    self.password = db_password

    db_host = os.environ.get("DB_HOST")
    if db_host is None:
      raise Exception("DB host is not set")
    self.host = db_host

    db_port = os.environ.get("DB_PORT")
    if db_port is None:
      raise Exception("DB post is not set")
    self.port = db_port
    
    db_name = os.environ.get("DB_NAME")
    if db_name is None:
      raise Exception("DB name is not set")
    self.name = db_name
