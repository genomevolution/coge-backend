from datetime import datetime

from sqlalchemy import case, func, or_

from model import Organism, Taxonomy
from repository.db import DB


MAX_ORGANISMS_PER_TAXONOMY = 5


class TaxonomyRepository:
    def __init__(self, db: DB):
        self.db = db

    def find_by_tax_id(self, tax_id: str):
        session = self.db.get_session()
        try:
            return session.query(Taxonomy).filter(Taxonomy.tax_id == tax_id).first()
        finally:
            session.close()

    def search(self, query: str, limit: int):
        session = self.db.get_session()
        try:
            normalized_query = query.lower()
            prefix = f"{normalized_query}%"
            taxonomies = (
                session.query(Taxonomy)
                .outerjoin(Organism, Organism.tax_id == Taxonomy.tax_id)
                .filter(or_(
                    Taxonomy.tax_id.like(prefix),
                    func.lower(Taxonomy.scientific_name).like(prefix),
                    func.lower(Organism.name).like(prefix)
                ))
                .order_by(
                    case((Taxonomy.tax_id == query, 0), else_=1),
                    func.lower(Taxonomy.scientific_name),
                    func.length(Taxonomy.tax_id),
                    Taxonomy.tax_id
                )
                .group_by(Taxonomy.tax_id)
                .limit(limit)
                .all()
            )

            matches = []
            for taxonomy in taxonomies:
                organism_query = session.query(Organism).filter(
                    Organism.tax_id == taxonomy.tax_id
                )
                taxonomy_matches = (
                    taxonomy.tax_id.lower().startswith(normalized_query)
                    or taxonomy.scientific_name.lower().startswith(normalized_query)
                )
                if not taxonomy_matches:
                    organism_query = organism_query.filter(
                        func.lower(Organism.name).like(prefix)
                    )
                organisms = (
                    organism_query
                    .order_by(func.lower(Organism.name), Organism.id)
                    .limit(MAX_ORGANISMS_PER_TAXONOMY)
                    .all()
                )
                matches.append((taxonomy, organisms))
            return matches
        finally:
            session.close()

    def create(self, tax_id: str, scientific_name: str):
        session = self.db.get_session()
        try:
            taxonomy = Taxonomy(
                tax_id=tax_id,
                scientific_name=scientific_name,
                created_at=datetime.utcnow()
            )
            session.add(taxonomy)
            session.commit()
            session.refresh(taxonomy)
            return taxonomy
        finally:
            session.close()
