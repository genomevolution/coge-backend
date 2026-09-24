from model.exceptions.entity_not_found import EntityNotFoundException
from repository.taxonomy import TaxonomyRepository
from service.request_validation import normalize_tax_id


DEFAULT_SEARCH_LIMIT = 8
MAX_SEARCH_LIMIT = 20


class TaxonomyService:
    def __init__(self, repository: TaxonomyRepository):
        self.repository = repository

    def get_by_tax_id(self, tax_id: str):
        taxonomy = self.repository.find_by_tax_id(normalize_tax_id(tax_id))
        if taxonomy is None:
            raise EntityNotFoundException("Taxonomy not found")
        return taxonomy.to_dict()

    def search(self, query: str, limit: int = DEFAULT_SEARCH_LIMIT):
        normalized_query = query.strip()
        if not normalized_query:
            raise ValueError("Search query is required")
        if len(normalized_query) > 256:
            raise ValueError("Search query must be 256 characters or fewer")
        if normalized_query.isdigit():
            normalized_query = normalize_tax_id(normalized_query)
        normalized_limit = max(1, min(limit, MAX_SEARCH_LIMIT))
        matches = self.repository.search(
            normalized_query,
            normalized_limit
        )
        return [
            {
                **taxonomy.to_dict(),
                "organisms": [
                    {"id": organism.id, "name": organism.name}
                    for organism in organisms
                ]
            }
            for taxonomy, organisms in matches
        ]
