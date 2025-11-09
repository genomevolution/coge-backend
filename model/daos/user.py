from sqlalchemy import Column, String
from model.daos.base import Base

class User(Base):
    __tablename__ = 'users'
    __table_args__ = {'schema': 'auth'}

    id = Column(String(36), primary_key=True)

    def to_dict(self):
        return {
            "id": self.id
        }
