import json
from datetime import datetime
from typing import Optional
import uuid

from fastapi import UploadFile

from model.exceptions.entity_not_found import EntityNotFoundException
from model.exceptions.invalid_file_type import InvalidFileTypeException
from repository.data_import import DataImportRepository
from repository.organism import OrganismRepository
from service.annotation_uploader_service import ANNOTATION_ALLOWED_EXTENSIONS
from service.genome_uploader_service import GENOME_ALLOWED_EXTENSIONS
from service.import_status import ImportComponent, ImportMode, ImportStatus
from service.minio_service import MinIOService
from service.nextflow_executor_service import NextflowExecutorService
from service.request_validation import validate_required_fields


ORGANISM_REQUIRED_FIELDS = ("name", "taxId", "speciesName")
GENOME_REQUIRED_FIELDS = ("name", "description", "accessionId", "sourceId")
ANNOTATION_REQUIRED_FIELDS = ("name", "description")
IMPORT_STAGING_PREFIX = "staging/imports/{import_id}/"


class DataImportService:
    def __init__(
        self,
        repository: DataImportRepository,
        organism_repository: OrganismRepository,
        minio_service: MinIOService,
        nextflow_executor: NextflowExecutorService
    ):
        self.repository = repository
        self.organism_repository = organism_repository
        self.minio_service = minio_service
        self.nextflow_executor = nextflow_executor

    def create_import(
        self,
        payload_json: str,
        fasta: Optional[UploadFile],
        gff3: Optional[UploadFile]
    ):
        payload = self._parse_and_validate_payload(payload_json, fasta, gff3)
        import_id = str(uuid.uuid4())
        planned_organism_id = (
            str(uuid.uuid4())
            if payload["mode"] == ImportMode.CREATE_ORGANISM.value
            else payload["targetOrganismId"]
        )
        planned_genome_id = str(uuid.uuid4()) if payload.get("genome") else None
        planned_annotation_id = str(uuid.uuid4()) if payload.get("annotation") else None
        metadata = {}
        fasta_path = None
        gff3_path = None

        try:
            if fasta is not None:
                fasta_path = self._upload_staged_file(import_id, "input", fasta)
                metadata["fasta_file_name"] = fasta.filename
            if gff3 is not None:
                gff3_path = self._upload_staged_file(import_id, "input", gff3)
                metadata["gff3_file_name"] = gff3.filename

            now = datetime.utcnow()
            data_import = self.repository.create_import({
                "id": import_id,
                "mode": payload["mode"],
                "status": ImportStatus.QUEUED.value,
                "phase": ImportStatus.QUEUED.value,
                "progress": 0,
                "payload": payload,
                "target_organism_id": payload.get("targetOrganismId"),
                "planned_organism_id": planned_organism_id,
                "planned_genome_id": planned_genome_id,
                "planned_annotation_id": planned_annotation_id,
                "fasta_path": fasta_path,
                "gff3_path": gff3_path,
                "execution_metadata": metadata,
                "created_at": now,
                "updated_at": now
            })
            return data_import.to_dict()
        except Exception:
            self.minio_service.delete_prefix(
                IMPORT_STAGING_PREFIX.format(import_id=import_id)
            )
            raise

    def get_active_imports(self):
        return [item.to_dict() for item in self.repository.get_active_imports()]

    def get_import(self, import_id: str):
        return self._require_import(import_id).to_dict()

    def replace_fasta(self, import_id: str, file: UploadFile):
        data_import = self._require_import(import_id)
        self._require_action_for_component(data_import, ImportComponent.FASTA)
        self._validate_extension(file.filename, GENOME_ALLOWED_EXTENSIONS)
        self._delete_processed_files(data_import)
        if data_import.fasta_path:
            self.minio_service.delete_file(data_import.fasta_path)
        path = self._upload_staged_file(import_id, "input", file)
        metadata = dict(data_import.execution_metadata or {})
        metadata.update({
            "fasta_file_name": file.filename,
            "genome_files": [],
            "annotation_files": [],
            "genome_generated_files": {}
        })
        updated = self.repository.update(
            import_id,
            fasta_path=path,
            status=ImportStatus.QUEUED.value,
            phase=ImportStatus.QUEUED.value,
            progress=0,
            current_execution_id=None,
            current_execution_type=None,
            failed_component=None,
            error_message=None,
            execution_metadata=metadata,
            completed_at=None
        )
        return updated.to_dict()

    def replace_gff3(self, import_id: str, file: UploadFile):
        data_import = self._require_import(import_id)
        self._require_action_for_component(data_import, ImportComponent.GFF3)
        if data_import.payload.get("annotation") is None:
            raise ValueError("This import no longer includes an annotation")
        self._validate_extension(file.filename, ANNOTATION_ALLOWED_EXTENSIONS)
        self._delete_processed_files(data_import, category="annotation")
        if data_import.gff3_path:
            self.minio_service.delete_file(data_import.gff3_path)
        path = self._upload_staged_file(import_id, "input", file)
        metadata = dict(data_import.execution_metadata or {})
        metadata.update({"gff3_file_name": file.filename, "annotation_files": []})
        next_status = (
            ImportStatus.VALIDATING_GFF3.value
            if metadata.get("genome_generated_files")
            else ImportStatus.QUEUED.value
        )
        updated = self.repository.update(
            import_id,
            gff3_path=path,
            status=next_status,
            phase=next_status,
            progress=60 if next_status == ImportStatus.VALIDATING_GFF3.value else 0,
            current_execution_id=None,
            current_execution_type=None,
            failed_component=None,
            error_message=None,
            execution_metadata=metadata,
            completed_at=None
        )
        return updated.to_dict()

    def remove_annotation(self, import_id: str):
        data_import = self._require_import(import_id)
        self._require_action_for_component(data_import, ImportComponent.GFF3)
        self._delete_processed_files(data_import, category="annotation")
        payload = dict(data_import.payload)
        payload["annotation"] = None
        if data_import.gff3_path:
            self.minio_service.delete_file(data_import.gff3_path)
        metadata = dict(data_import.execution_metadata or {})
        metadata["annotation_files"] = []
        next_status = (
            ImportStatus.PUBLISHING.value
            if metadata.get("genome_files")
            else ImportStatus.QUEUED.value
        )
        updated = self.repository.update(
            import_id,
            payload=payload,
            gff3_path=None,
            planned_annotation_id=None,
            status=next_status,
            phase=next_status,
            progress=95 if next_status == ImportStatus.PUBLISHING.value else 0,
            current_execution_id=None,
            current_execution_type=None,
            failed_component=None,
            error_message=None,
            execution_metadata=metadata,
            completed_at=None
        )
        return updated.to_dict()

    def retry_import(self, import_id: str):
        data_import = self._require_import(import_id)
        if data_import.status != ImportStatus.FAILED_RETRYABLE.value:
            raise ValueError("Only retryable imports can be retried")
        metadata = data_import.execution_metadata or {}
        if metadata.get("annotation_files") or (
            metadata.get("genome_files") and not data_import.payload.get("annotation")
        ):
            next_status = ImportStatus.PUBLISHING.value
        elif metadata.get("genome_generated_files") and data_import.payload.get("annotation"):
            next_status = ImportStatus.VALIDATING_GFF3.value
        else:
            next_status = ImportStatus.QUEUED.value
        updated = self.repository.update(
            import_id,
            status=next_status,
            phase=next_status,
            current_execution_id=None,
            current_execution_type=None,
            failed_component=None,
            error_message=None,
            completed_at=None
        )
        return updated.to_dict()

    def cancel_import(self, import_id: str):
        data_import = self._require_import(import_id)
        if data_import.status in (
            ImportStatus.PUBLISHED.value,
            ImportStatus.CANCELLED.value
        ):
            raise ValueError("Completed imports cannot be cancelled")
        if data_import.current_execution_id:
            self.nextflow_executor.cancel_execution(data_import.current_execution_id)
        self.minio_service.delete_prefix(
            IMPORT_STAGING_PREFIX.format(import_id=import_id)
        )
        self._delete_processed_files(data_import)
        now = datetime.utcnow()
        updated = self.repository.update(
            import_id,
            status=ImportStatus.CANCELLED.value,
            phase=ImportStatus.CANCELLED.value,
            current_execution_id=None,
            current_execution_type=None,
            completed_at=now
        )
        return updated.to_dict()

    def _parse_and_validate_payload(self, payload_json, fasta, gff3):
        try:
            payload = json.loads(payload_json)
        except (TypeError, json.JSONDecodeError) as error:
            raise ValueError("Payload must be valid JSON") from error

        mode = payload.get("mode")
        if mode not in (ImportMode.CREATE_ORGANISM.value, ImportMode.ADD_GENOME.value):
            raise ValueError("Unsupported import mode")
        if mode == ImportMode.CREATE_ORGANISM.value:
            validate_required_fields(payload.get("organism"), ORGANISM_REQUIRED_FIELDS)
            organism = payload["organism"]
            if self.organism_repository.find_organism_by_identity(
                organism["name"], organism["taxId"], organism["speciesName"]
            ) is not None:
                raise ValueError("An organism with the same identity already exists")
        else:
            target_id = payload.get("targetOrganismId")
            if not target_id:
                raise ValueError("targetOrganismId is required")
            self.organism_repository.get_organism_by_id(target_id)

        genome = payload.get("genome")
        annotation = payload.get("annotation")
        if mode == ImportMode.ADD_GENOME.value and genome is None:
            raise ValueError("A genome is required when adding to an organism")
        if genome is not None:
            validate_required_fields(genome, GENOME_REQUIRED_FIELDS)
            if fasta is None:
                raise ValueError("A FASTA file is required")
            self._validate_extension(fasta.filename, GENOME_ALLOWED_EXTENSIONS)
        elif fasta is not None or annotation is not None or gff3 is not None:
            raise ValueError("Genome data is required when files or annotation are included")
        if annotation is not None:
            validate_required_fields(annotation, ANNOTATION_REQUIRED_FIELDS)
            if gff3 is None:
                raise ValueError("A GFF3 file is required")
            self._validate_extension(gff3.filename, ANNOTATION_ALLOWED_EXTENSIONS)
        elif gff3 is not None:
            raise ValueError("Annotation metadata is required for a GFF3 file")
        return payload

    def _upload_staged_file(self, import_id, category, file):
        path = self.minio_service.generate_import_staging_path(
            import_id,
            category,
            file.filename
        )
        file.file.seek(0, 2)
        file_size = file.file.tell()
        file.file.seek(0)
        self.minio_service.upload_file(
            file.file,
            path,
            file.content_type or "application/octet-stream",
            file_size
        )
        return path

    def _validate_extension(self, filename, extensions):
        if not filename or not any(
            filename.lower().endswith(extension) for extension in extensions
        ):
            raise InvalidFileTypeException(filename or "", list(extensions))

    def _require_import(self, import_id):
        data_import = self.repository.get_by_id(import_id)
        if data_import is None:
            raise EntityNotFoundException("Import not found")
        return data_import

    def _delete_processed_files(self, data_import, category=None):
        metadata = data_import.execution_metadata or {}
        keys = []
        if category in (None, "genome"):
            keys.append("genome_files")
        if category in (None, "annotation"):
            keys.append("annotation_files")
        for key in keys:
            for file_values in metadata.get(key, []):
                path = file_values.get("path")
                if path:
                    self.minio_service.delete_file(path)

    def _require_action_for_component(self, data_import, component):
        if (
            data_import.status != ImportStatus.ACTION_REQUIRED.value
            or data_import.failed_component != component.value
        ):
            raise ValueError(
                f"This import is not waiting for a replacement {component.value} file"
            )
