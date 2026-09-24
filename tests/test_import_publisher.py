from unittest.mock import MagicMock

from repository.import_publisher import ImportPublisherRepository
from service.import_status import ImportMode


def test_publisher_reuses_organism_created_by_concurrent_import():
  taxonomy = MagicMock(scientific_name="Leishmania braziliensis")
  existing_organism = MagicMock(id="organism-1")
  session = MagicMock()
  session.query.return_value.filter.return_value.first.side_effect = [
    taxonomy,
    existing_organism
  ]
  data_import = MagicMock(
    mode=ImportMode.CREATE_ORGANISM.value,
    planned_organism_id="planned-organism"
  )
  publisher = ImportPublisherRepository(MagicMock())
  payload = {
    "organism": {
      "name": "UN0010",
      "taxId": "5660",
      "speciesName": "Leishmania braziliensis"
    }
  }

  result = publisher._resolve_organism(session, data_import, payload, MagicMock())

  assert result is existing_organism
  session.execute.assert_called_once()
  session.add.assert_not_called()


def test_publisher_creates_organism_when_tax_id_is_new():
  session = MagicMock()
  session.query.return_value.filter.return_value.first.side_effect = [None, None]
  data_import = MagicMock(
    mode=ImportMode.CREATE_ORGANISM.value,
    planned_organism_id="planned-organism"
  )
  publisher = ImportPublisherRepository(MagicMock())
  payload = {
    "organism": {
      "name": "UN0010",
      "taxId": "5660",
      "speciesName": "Leishmania braziliensis"
    }
  }

  result = publisher._resolve_organism(session, data_import, payload, MagicMock())

  assert result.id == "planned-organism"
  assert result.tax_id == "5660"
  assert result.species_name == "Leishmania braziliensis"
  assert session.add.call_count == 2
  assert session.flush.call_count == 2
