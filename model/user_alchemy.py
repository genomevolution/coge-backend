from sqlalchemy import Column, String
from sqlalchemy.orm import relationship
from model.base_alchemy import Base


class UserAlchemy(Base):
    __tablename__ = 'users'
    __table_args__ = {'schema': 'auth'}

    id = Column(String(36), primary_key=True)

    organisms = relationship("OrganismAlchemy", back_populates="user", lazy='noload')

    def to_dict(self):
        return {
            "id": self.id
        }

