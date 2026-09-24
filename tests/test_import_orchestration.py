import json
from unittest.mock import MagicMock

import pytest

from service.data_import import DataImportService
from service.import_coordinator import ImportCoordinatorService
from service.import_status import ImportComponent, ImportMode, ImportStatus


class FakeImport:
  def __init__(self, **values):
    defaults = {
      "id": "import-1",
      "status": ImportStatus.QUEUED.value,
      "phase": ImportStatus.QUEUED.value,
      "payload": {},
      "failed_component": None,
      "fasta_path": None,
      "gff3_path": None,
      "current_execution_id": None,
      "current_execution_type": None,
      "execution_metadata": {},
      "planned_organism_id": "organism-1",
      "planned_genome_id": "genome-1",
      "planned_annotation_id": "annotation-1"
    }
    defaults.update(values)
    for key, value in defaults.items():
      setattr(self, key, value)

  def to_dict(self):
    return {"id": self.id, "status": self.status}


class UpdatingRepository:
  def __init__(self, data_import):
    self.data_import = data_import
    self.updates = []

  def get_by_id(self, _import_id):
    return self.data_import

  def update(self, _import_id, **values):
    self.updates.append(values)
    for key, value in values.items():
      setattr(self.data_import, key, value)
    return self.data_import


def test_organism_without_genome_moves_directly_to_publication(tmp_path):
  data_import = FakeImport(payload={"organism": {"name": "test"}})
  repository = UpdatingRepository(data_import)
  coordinator = ImportCoordinatorService(
    repository,
    MagicMock(),
    MagicMock(),
    MagicMock()
  )
  coordinator.temp_root = tmp_path

  coordinator.process_import(data_import)

  assert data_import.status == ImportStatus.PUBLISHING.value
  assert data_import.progress == 95


def test_gff3_validation_failure_requires_user_action(tmp_path):
  data_import = FakeImport(
    status=ImportStatus.VALIDATING_GFF3.value,
    phase=ImportStatus.VALIDATING_GFF3.value,
    current_execution_id="execution-1"
  )
  repository = UpdatingRepository(data_import)
  executor = MagicMock()
  executor.get_execution_status.return_value = {
    "status": "FAILED",
    "error_message": "process failed",
    "logs": "VALIDATION_ERROR: unknown sequence ID"
  }
  coordinator = ImportCoordinatorService(
    repository,
    MagicMock(),
    MagicMock(),
    executor
  )
  coordinator.temp_root = tmp_path

  coordinator.process_import(data_import)

  assert data_import.status == ImportStatus.ACTION_REQUIRED.value
  assert data_import.failed_component == ImportComponent.GFF3.value
  assert data_import.error_message == "unknown sequence ID"


def test_removing_invalid_annotation_resumes_publication():
  staged_gff3_path = "staging/imports/import-1/input/annotation.gff3"
  data_import = FakeImport(
    status=ImportStatus.ACTION_REQUIRED.value,
    phase=ImportStatus.ACTION_REQUIRED.value,
    failed_component=ImportComponent.GFF3.value,
    gff3_path=staged_gff3_path,
    payload={
      "genome": {"name": "v1"},
      "annotation": {"name": "v1"}
    },
    execution_metadata={
      "genome_files": [{"path": "organism-1/genomes/genome.fa.gz"}],
      "annotation_files": []
    }
  )
  repository = UpdatingRepository(data_import)
  minio_service = MagicMock()
  service = DataImportService(
    repository,
    MagicMock(),
    MagicMock(),
    minio_service,
    MagicMock()
  )

  service.remove_annotation(data_import.id)

  assert data_import.payload["annotation"] is None
  assert data_import.status == ImportStatus.PUBLISHING.value
  assert data_import.failed_component is None
  minio_service.delete_file.assert_called_once_with(staged_gff3_path)


def test_cancel_stops_execution_and_cleans_staging():
  data_import = FakeImport(
    status=ImportStatus.PROCESSING_FASTA.value,
    current_execution_id="execution-1",
    execution_metadata={"genome_files": [], "annotation_files": []}
  )
  repository = UpdatingRepository(data_import)
  minio_service = MagicMock()
  executor = MagicMock()
  service = DataImportService(
    repository,
    MagicMock(),
    MagicMock(),
    minio_service,
    executor
  )

  service.cancel_import(data_import.id)

  executor.cancel_execution.assert_called_once_with("execution-1")
  minio_service.delete_prefix.assert_called_once_with("staging/imports/import-1/")
  assert data_import.status == ImportStatus.CANCELLED.value


def test_existing_organism_must_be_selected_instead_of_created_again():
  existing_organism = MagicMock()
  existing_organism.id = "organism-1"
  existing_organism.to_dict.return_value = {
    "id": "organism-1",
    "name": "UN0010",
    "taxId": "5660",
    "speciesName": "Leishmania braziliensis",
    "metadata": {"host": "Homo sapiens"}
  }
  organism_repository = MagicMock()
  organism_repository.find_organism_by_name_and_tax_id.return_value = existing_organism
  taxonomy_repository = MagicMock()
  taxonomy_repository.find_by_tax_id.return_value = MagicMock(
    scientific_name="Leishmania braziliensis"
  )
  service = DataImportService(
    MagicMock(),
    organism_repository,
    taxonomy_repository,
    MagicMock(),
    MagicMock()
  )
  fasta = MagicMock(filename="genome.fa")

  with pytest.raises(ValueError, match="already exists.*search"):
    service._parse_and_validate_payload(json.dumps({
      "mode": ImportMode.CREATE_ORGANISM.value,
      "organism": {
        "name": "UN0010",
        "taxId": "05660",
        "speciesName": "Mistyped species"
      },
      "genome": {
        "name": "v2",
        "description": "New sequencing",
        "accessionId": "GCA_2",
        "sourceId": "source-1"
      }
    }), fasta, None)

  organism_repository.find_organism_by_name_and_tax_id.assert_called_once_with(
    "UN0010",
    "5660"
  )
  organism_repository.get_organism_by_id.assert_not_called()


def test_new_tax_id_keeps_create_organism_mode():
  organism_repository = MagicMock()
  organism_repository.find_organism_by_name_and_tax_id.return_value = None
  taxonomy_repository = MagicMock()
  taxonomy_repository.find_by_tax_id.return_value = None
  service = DataImportService(
    MagicMock(),
    organism_repository,
    taxonomy_repository,
    MagicMock(),
    MagicMock()
  )

  payload = service._parse_and_validate_payload(json.dumps({
    "mode": ImportMode.CREATE_ORGANISM.value,
    "organism": {
      "name": "UN0010",
      "taxId": "05660",
      "speciesName": "Leishmania braziliensis"
    }
  }), None, None)

  assert payload["mode"] == ImportMode.CREATE_ORGANISM.value
  assert payload["organism"]["taxId"] == "5660"


def test_existing_tax_id_without_genome_is_rejected():
  organism_repository = MagicMock()
  organism_repository.find_organism_by_name_and_tax_id.return_value = MagicMock(
    id="organism-1"
  )
  service = DataImportService(
    MagicMock(),
    organism_repository,
    MagicMock(),
    MagicMock(),
    MagicMock()
  )

  with pytest.raises(ValueError, match="already exists.*search"):
    service._parse_and_validate_payload(json.dumps({
      "mode": ImportMode.CREATE_ORGANISM.value,
      "organism": {
        "name": "UN0010",
        "taxId": "5660",
        "speciesName": "Leishmania braziliensis"
      }
    }), None, None)


def test_same_tax_id_with_different_organism_name_creates_new_organism():
  organism_repository = MagicMock()
  organism_repository.find_organism_by_name_and_tax_id.return_value = None
  taxonomy_repository = MagicMock()
  taxonomy_repository.find_by_tax_id.return_value = MagicMock(
    scientific_name="Leishmania braziliensis"
  )
  service = DataImportService(
    MagicMock(),
    organism_repository,
    taxonomy_repository,
    MagicMock(),
    MagicMock()
  )

  payload = service._parse_and_validate_payload(json.dumps({
    "mode": ImportMode.CREATE_ORGANISM.value,
    "organism": {
      "name": "ANOTHER_ISOLATE",
      "taxId": "5660",
      "speciesName": "Typo braziliensis"
    }
  }), None, None)

  assert payload["mode"] == ImportMode.CREATE_ORGANISM.value
  assert payload["organism"]["speciesName"] == "Leishmania braziliensis"
