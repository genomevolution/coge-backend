import gzip
import logging
import os
import re
import shutil
from pathlib import Path

from config import config
from repository.data_import import DataImportRepository
from repository.import_publisher import ImportPublisherRepository
from service.execution_status import ExecutionStatus
from service.import_status import (
    ImportComponent,
    ImportExecutionType,
    ImportStatus
)
from service.minio_service import MinIOService
from service.nextflow_executor_service import NextflowExecutorService


DOWNLOAD_CHUNK_SIZE_BYTES = 8 * 1024 * 1024
ANSI_ESCAPE_PATTERN = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
logger = logging.getLogger(__name__)
GENOME_FILE_TYPES = {
    "fasta_gz": ("FASTA_GZ", "application/gzip"),
    "gzi_index": ("GZI", "application/octet-stream"),
    "fai_index": ("FAI", "text/plain")
}
ANNOTATION_FILE_TYPES = {
    "gff3_gz": ("GFF3_GZ", "application/gzip"),
    "tabix_index": ("TBI", "application/octet-stream")
}


class ImportCoordinatorService:
    def __init__(
        self,
        repository: DataImportRepository,
        publisher: ImportPublisherRepository,
        minio_service: MinIOService,
        nextflow_executor: NextflowExecutorService
    ):
        self.repository = repository
        self.publisher = publisher
        self.minio_service = minio_service
        self.nextflow_executor = nextflow_executor
        self.temp_root = Path(config.PROCESSING_TEMP_DIR) / "imports"
        self.temp_root.mkdir(parents=True, exist_ok=True)

    def process_import(self, data_import):
        try:
            handlers = {
                ImportStatus.QUEUED.value: self._process_queued,
                ImportStatus.VALIDATING_FASTA.value: self._monitor_fasta_validation,
                ImportStatus.PROCESSING_FASTA.value: self._monitor_fasta_processing,
                ImportStatus.VALIDATING_GFF3.value: self._monitor_gff3_validation,
                ImportStatus.PROCESSING_GFF3.value: self._monitor_gff3_processing,
                ImportStatus.PUBLISHING.value: self._publish
            }
            handler = handlers.get(data_import.status)
            if handler:
                handler(data_import)
        except Exception as error:
            self.repository.update(
                data_import.id,
                status=ImportStatus.FAILED_RETRYABLE.value,
                phase=ImportStatus.FAILED_RETRYABLE.value,
                failed_component=ImportComponent.INFRASTRUCTURE.value,
                error_message=str(error),
                current_execution_id=None,
                current_execution_type=None
            )

    def cleanup_import(self, import_id):
        self.minio_service.delete_prefix(f"staging/imports/{import_id}/")
        shutil.rmtree(self.temp_root / import_id, ignore_errors=True)

    def cleanup_failed_import(self, data_import):
        metadata = data_import.execution_metadata or {}
        for key in ("genome_files", "annotation_files"):
            for file_values in metadata.get(key, []):
                path = file_values.get("path")
                if path:
                    self.minio_service.delete_file(path)
        self.cleanup_import(data_import.id)

    def _process_queued(self, data_import):
        if data_import.payload.get("genome") is None:
            self.repository.update(
                data_import.id,
                status=ImportStatus.PUBLISHING.value,
                phase=ImportStatus.PUBLISHING.value,
                progress=95
            )
            return
        self._launch_fasta_validation(data_import)

    def _launch_fasta_validation(self, data_import):
        import_dir = self._import_dir(data_import.id)
        fasta_path = str(import_dir / "input.fa")
        try:
            self._download_file(data_import.fasta_path, fasta_path)
        except (gzip.BadGzipFile, EOFError) as error:
            self.repository.update(
                data_import.id,
                status=ImportStatus.ACTION_REQUIRED.value,
                phase=ImportStatus.ACTION_REQUIRED.value,
                failed_component=ImportComponent.FASTA.value,
                error_message=f"Invalid compressed FASTA: {error}"
            )
            return
        execution_id = self.nextflow_executor.execute_import_validation(
            data_import.id,
            ImportComponent.FASTA.value,
            fasta_path
        )
        metadata = self._merge_metadata(data_import, {"local_fasta_path": fasta_path})
        self.repository.update(
            data_import.id,
            status=ImportStatus.VALIDATING_FASTA.value,
            phase=ImportStatus.VALIDATING_FASTA.value,
            progress=5,
            current_execution_id=execution_id,
            current_execution_type=ImportExecutionType.FASTA_VALIDATION.value,
            execution_metadata=metadata
        )

    def _monitor_fasta_validation(self, data_import):
        status = self._execution_status(data_import)
        if status["status"] == ExecutionStatus.RUNNING.value:
            self._update_progress(data_import.id, 5, 15, status.get("progress", 0))
            return
        if status["status"] != ExecutionStatus.COMPLETED.value:
            self._require_action(data_import, ImportComponent.FASTA, status)
            return

        metadata = data_import.execution_metadata or {}
        execution_id = self.nextflow_executor.execute_genome_indexing(
            organism_id=data_import.planned_organism_id,
            genome_id=data_import.planned_genome_id,
            fasta_local_path=metadata["local_fasta_path"],
            profile="standard"
        )
        self.repository.update(
            data_import.id,
            status=ImportStatus.PROCESSING_FASTA.value,
            phase=ImportStatus.PROCESSING_FASTA.value,
            progress=15,
            current_execution_id=execution_id,
            current_execution_type=ImportExecutionType.FASTA_PROCESSING.value
        )

    def _monitor_fasta_processing(self, data_import):
        status = self._execution_status(data_import)
        if status["status"] == ExecutionStatus.RUNNING.value:
            self._update_progress(data_import.id, 15, 55, status.get("progress", 0))
            return
        if status["status"] != ExecutionStatus.COMPLETED.value:
            self._require_action(data_import, ImportComponent.FASTA, status)
            return

        generated_files = status.get("generated_files", {})
        uploaded_files = self._upload_generated_files(
            data_import,
            generated_files,
            GENOME_FILE_TYPES,
            "genome"
        )
        metadata = self._merge_metadata(data_import, {
            "genome_generated_files": generated_files,
            "genome_files": uploaded_files
        })
        if data_import.payload.get("annotation"):
            self.repository.update(
                data_import.id,
                status=ImportStatus.VALIDATING_GFF3.value,
                phase=ImportStatus.VALIDATING_GFF3.value,
                progress=60,
                current_execution_id=None,
                current_execution_type=None,
                execution_metadata=metadata
            )
        else:
            self.repository.update(
                data_import.id,
                status=ImportStatus.PUBLISHING.value,
                phase=ImportStatus.PUBLISHING.value,
                progress=95,
                current_execution_id=None,
                current_execution_type=None,
                execution_metadata=metadata
            )

    def _monitor_gff3_validation(self, data_import):
        if data_import.current_execution_id is None:
            self._launch_gff3_validation(data_import)
            return
        status = self._execution_status(data_import)
        if status["status"] == ExecutionStatus.RUNNING.value:
            self._update_progress(data_import.id, 60, 65, status.get("progress", 0))
            return
        if status["status"] != ExecutionStatus.COMPLETED.value:
            self._require_action(data_import, ImportComponent.GFF3, status)
            return

        metadata = data_import.execution_metadata or {}
        execution_id = self.nextflow_executor.execute_annotation_processing(
            organism_id=data_import.planned_organism_id,
            genome_id=data_import.planned_genome_id,
            annotation_id=data_import.planned_annotation_id,
            gff3_local_path=metadata["local_gff3_path"],
            profile="standard"
        )
        self.repository.update(
            data_import.id,
            status=ImportStatus.PROCESSING_GFF3.value,
            phase=ImportStatus.PROCESSING_GFF3.value,
            progress=65,
            current_execution_id=execution_id,
            current_execution_type=ImportExecutionType.GFF3_PROCESSING.value
        )

    def _launch_gff3_validation(self, data_import):
        import_dir = self._import_dir(data_import.id)
        gff3_path = str(import_dir / "input.gff3")
        try:
            self._download_file(data_import.gff3_path, gff3_path)
        except (gzip.BadGzipFile, EOFError) as error:
            self.repository.update(
                data_import.id,
                status=ImportStatus.ACTION_REQUIRED.value,
                phase=ImportStatus.ACTION_REQUIRED.value,
                failed_component=ImportComponent.GFF3.value,
                error_message=f"Invalid compressed GFF3: {error}"
            )
            return
        generated = (data_import.execution_metadata or {}).get("genome_generated_files", {})
        fai_path = generated.get("fai_index")
        if not fai_path:
            raise ValueError("The processed FASTA index is missing")
        execution_id = self.nextflow_executor.execute_import_validation(
            data_import.id,
            ImportComponent.GFF3.value,
            gff3_path,
            fai_local_path=fai_path
        )
        metadata = self._merge_metadata(data_import, {"local_gff3_path": gff3_path})
        self.repository.update(
            data_import.id,
            current_execution_id=execution_id,
            current_execution_type=ImportExecutionType.GFF3_VALIDATION.value,
            execution_metadata=metadata
        )

    def _monitor_gff3_processing(self, data_import):
        status = self._execution_status(data_import)
        if status["status"] == ExecutionStatus.RUNNING.value:
            self._update_progress(data_import.id, 65, 90, status.get("progress", 0))
            return
        if status["status"] != ExecutionStatus.COMPLETED.value:
            self._require_action(data_import, ImportComponent.GFF3, status)
            return
        uploaded_files = self._upload_generated_files(
            data_import,
            status.get("generated_files", {}),
            ANNOTATION_FILE_TYPES,
            "annotation"
        )
        metadata = self._merge_metadata(data_import, {"annotation_files": uploaded_files})
        self.repository.update(
            data_import.id,
            status=ImportStatus.PUBLISHING.value,
            phase=ImportStatus.PUBLISHING.value,
            progress=95,
            current_execution_id=None,
            current_execution_type=None,
            execution_metadata=metadata
        )

    def _publish(self, data_import):
        self.publisher.publish(data_import.id)
        try:
            self.cleanup_import(data_import.id)
        except Exception:
            logger.warning(
                "Published import %s but could not clean staging data",
                data_import.id,
                exc_info=True
            )

    def _upload_generated_files(self, data_import, generated, type_mapping, category):
        uploaded = []
        for generated_type, (database_type, content_type) in type_mapping.items():
            local_path = generated.get(generated_type)
            if not local_path or not Path(local_path).exists():
                raise ValueError(f"Expected generated file is missing: {generated_type}")
            file_name = Path(local_path).name
            if category == "genome":
                destination = self.minio_service.generate_genome_file_path(
                    data_import.planned_organism_id,
                    file_name
                )
            else:
                destination = self.minio_service.generate_annotation_file_path(
                    data_import.planned_annotation_id,
                    file_name
                )
            with open(local_path, "rb") as local_file:
                size = os.path.getsize(local_path)
                self.minio_service.upload_file(
                    local_file,
                    destination,
                    content_type,
                    size
                )
            uploaded.append({
                "path": destination,
                "type": database_type,
                "metadata": {
                    "original_filename": file_name,
                    "file_size": size,
                    "content_type": content_type,
                    "generated": True,
                    "import_id": data_import.id
                }
            })
        return uploaded

    def _execution_status(self, data_import):
        if not data_import.current_execution_id:
            raise ValueError("Import execution ID is missing")
        return self.nextflow_executor.get_execution_status(
            data_import.current_execution_id
        )

    def _require_action(self, data_import, component, status):
        error_message = self._validation_error_from_logs(
            status.get("logs", "")
        ) or status.get("error_message") or f"{component.value} processing failed"
        self.repository.update(
            data_import.id,
            status=ImportStatus.ACTION_REQUIRED.value,
            phase=ImportStatus.ACTION_REQUIRED.value,
            failed_component=component.value,
            error_message=error_message,
            current_execution_id=None,
            current_execution_type=None
        )

    def _validation_error_from_logs(self, logs):
        for line in reversed(logs.splitlines()):
            if "VALIDATION_ERROR:" in line:
                message = line.split("VALIDATION_ERROR:", 1)[1].strip()
                return ANSI_ESCAPE_PATTERN.sub("", message)
        return None

    def _update_progress(self, import_id, minimum, maximum, execution_progress):
        progress = minimum + int((maximum - minimum) * execution_progress / 100)
        self.repository.update(import_id, progress=progress)

    def _merge_metadata(self, data_import, values):
        metadata = dict(data_import.execution_metadata or {})
        metadata.update(values)
        return metadata

    def _import_dir(self, import_id):
        directory = self.temp_root / import_id
        directory.mkdir(parents=True, exist_ok=True)
        return directory

    def _download_file(self, minio_path, local_path):
        response = self.minio_service.download_file(minio_path)
        try:
            with open(local_path, "wb") as output_file:
                if minio_path.lower().endswith(".gz"):
                    with gzip.GzipFile(fileobj=response, mode="rb") as compressed:
                        shutil.copyfileobj(compressed, output_file, DOWNLOAD_CHUNK_SIZE_BYTES)
                else:
                    for chunk in response.stream(amt=DOWNLOAD_CHUNK_SIZE_BYTES):
                        output_file.write(chunk)
        finally:
            response.close()
            response.release_conn()
