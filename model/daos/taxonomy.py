from sqlalchemy import Column, ForeignKey, String, TIMESTAMP
from sqlalchemy.sql import func

from model.daos.base import Base


class Taxonomy(Base):
    __tablename__ = "taxonomy"
    __table_args__ = {"schema": "core"}

    tax_id = Column(String(36), primary_key=True)
    scientific_name = Column(String(256), nullable=False)
    parent_tax_id = Column(
        String(36),
        ForeignKey("core.taxonomy.tax_id", deferrable=True, initially="DEFERRED")
    )
    rank = Column(String(64))
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())

    def to_dict(self):
        return {
            "taxId": self.tax_id,
            "scientificName": self.scientific_name,
            "parentTaxId": self.parent_tax_id,
            "rank": self.rank,
            "createdAt": self.created_at.isoformat() if self.created_at else None
        }
