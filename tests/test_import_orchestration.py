from unittest.mock import MagicMock

from service.data_import import DataImportService
from service.import_coordinator import ImportCoordinatorService
from service.import_status import ImportComponent, ImportStatus


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
    minio_service,
    executor
  )

  service.cancel_import(data_import.id)

  executor.cancel_execution.assert_called_once_with("execution-1")
  minio_service.delete_prefix.assert_called_once_with("staging/imports/import-1/")
  assert data_import.status == ImportStatus.CANCELLED.value
