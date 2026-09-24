from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from model.exceptions.entity_not_found import EntityNotFoundException
from service.taxonomy import TaxonomyService


def test_taxonomy_lookup_returns_canonical_scientific_name():
  taxonomy = SimpleNamespace(
    to_dict=lambda: {
      "taxId": "5660",
      "scientificName": "Leishmania braziliensis"
    }
  )
  repository = MagicMock()
  repository.find_by_tax_id.return_value = taxonomy

  result = TaxonomyService(repository).get_by_tax_id("05660")

  assert result["scientificName"] == "Leishmania braziliensis"
  repository.find_by_tax_id.assert_called_once_with("5660")


def test_taxonomy_lookup_returns_not_found_for_unknown_tax_id():
  repository = MagicMock()
  repository.find_by_tax_id.return_value = None

  with pytest.raises(EntityNotFoundException):
    TaxonomyService(repository).get_by_tax_id("5660")


def test_taxonomy_search_returns_species_and_existing_organisms():
  taxonomy = SimpleNamespace(
    to_dict=lambda: {
      "taxId": "5660",
      "scientificName": "Leishmania braziliensis"
    }
  )
  organisms = [
    SimpleNamespace(id="organism-1", name="UN0010"),
    SimpleNamespace(id="organism-2", name="UN0079")
  ]
  repository = MagicMock()
  repository.search.return_value = [(taxonomy, organisms)]

  result = TaxonomyService(repository).search("056", 50)

  assert result == [{
    "taxId": "5660",
    "scientificName": "Leishmania braziliensis",
    "organisms": [
      {"id": "organism-1", "name": "UN0010"},
      {"id": "organism-2", "name": "UN0079"}
    ]
  }]
  repository.search.assert_called_once_with("56", 20)


@pytest.mark.parametrize("query", ["", "   ", "0"])
def test_taxonomy_search_rejects_invalid_query(query):
  repository = MagicMock()

  with pytest.raises(ValueError):
    TaxonomyService(repository).search(query)

  repository.search.assert_not_called()


@pytest.mark.parametrize("query", ["Leishmania", "un0010"])
def test_taxonomy_search_accepts_species_or_organism_name(query):
  repository = MagicMock()
  repository.search.return_value = []

  assert TaxonomyService(repository).search(query) == []
  repository.search.assert_called_once_with(query, 8)
