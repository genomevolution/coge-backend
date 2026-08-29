from datetime import datetime
import uuid

from sqlalchemy import func

from model import Annotation, AnnotationFile, DataImport, File, Genome, GenomeFile, Organism, Source
from model.exceptions.duplicate_entity import DuplicateEntityException
from model.exceptions.entity_not_found import EntityNotFoundException
from repository.db import DB
from service.import_status import ImportMode, ImportStatus


class ImportPublisherRepository:
    def __init__(self, db: DB):
        self.db = db

    def publish(self, import_id: str) -> str:
        session = self.db.get_session()
        try:
            data_import = (
                session.query(DataImport)
                .filter(DataImport.id == import_id)
                .with_for_update()
                .first()
            )
            if data_import is None:
                raise EntityNotFoundException("Import not found")
            if data_import.status == ImportStatus.PUBLISHED.value:
                return data_import.published_entity_id

            payload = data_import.payload
            now = datetime.utcnow()
            organism = self._resolve_organism(session, data_import, payload, now)
            genome = self._create_genome(session, data_import, payload, organism.id, now)
            annotation = self._create_annotation(
                session,
                data_import,
                payload,
                genome.id if genome else None,
                now
            )
            self._create_file_records(session, data_import, genome, annotation, now)

            published_entity_id = organism.id if data_import.mode == ImportMode.CREATE_ORGANISM.value else genome.id
            data_import.status = ImportStatus.PUBLISHED.value
            data_import.phase = ImportStatus.PUBLISHED.value
            data_import.progress = 100
            data_import.published_entity_id = published_entity_id
            data_import.error_message = None
            data_import.failed_component = None
            data_import.updated_at = now
            data_import.completed_at = now
            session.commit()
            return published_entity_id
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def _resolve_organism(self, session, data_import, payload, now):
        if data_import.mode == ImportMode.ADD_GENOME.value:
            organism = session.query(Organism).filter(
                Organism.id == data_import.target_organism_id
            ).first()
            if organism is None:
                raise EntityNotFoundException("Organism not found")
            return organism

        organism_payload = payload["organism"]
        duplicate = session.query(Organism.id).filter(
            Organism.tax_id == organism_payload["taxId"],
            func.lower(Organism.name) == organism_payload["name"].lower(),
            func.lower(Organism.species_name) == organism_payload["speciesName"].lower()
        ).first()
        if duplicate is not None:
            raise DuplicateEntityException(
                "An organism with the same name, taxonomy ID, and species already exists"
            )

        organism = Organism(
            id=data_import.planned_organism_id,
            name=organism_payload["name"],
            tax_id=organism_payload["taxId"],
            species_name=organism_payload["speciesName"],
            organism_metadata=organism_payload.get("metadata"),
            created_at=now
        )
        session.add(organism)
        session.flush()
        return organism

    def _create_genome(self, session, data_import, payload, organism_id, now):
        genome_payload = payload.get("genome")
        if genome_payload is None:
            return None

        source = session.query(Source).filter(
            Source.id == genome_payload["sourceId"]
        ).first()
        if source is None:
            raise EntityNotFoundException("Source not found")

        genome = Genome(
            id=data_import.planned_genome_id,
            organism_fk=organism_id,
            created_at=now,
            name=genome_payload["name"],
            description=genome_payload["description"],
            public=bool(genome_payload.get("public", True)),
            accesion_id=genome_payload["accessionId"],
            source_fk=genome_payload["sourceId"]
        )
        session.add(genome)
        session.flush()
        return genome

    def _create_annotation(self, session, data_import, payload, genome_id, now):
        annotation_payload = payload.get("annotation")
        if annotation_payload is None:
            return None
        if genome_id is None:
            raise ValueError("An annotation requires a genome")

        annotation = Annotation(
            id=data_import.planned_annotation_id,
            fk_genome=genome_id,
            created_at=now,
            name=annotation_payload["name"],
            description=annotation_payload["description"],
            public=bool(annotation_payload.get("public", True)),
            primary_annotation=True
        )
        session.add(annotation)
        session.flush()
        return annotation

    def _create_file_records(self, session, data_import, genome, annotation, now):
        metadata = data_import.execution_metadata or {}
        if genome is not None:
            for file_values in metadata.get("genome_files", []):
                file_record = self._create_file(session, file_values, now)
                session.add(GenomeFile(
                    id=str(uuid.uuid4()),
                    file_fk=file_record.id,
                    genome_fk=genome.id,
                    type=file_values["type"]
                ))

        if annotation is not None:
            for file_values in metadata.get("annotation_files", []):
                file_record = self._create_file(session, file_values, now)
                session.add(AnnotationFile(
                    id=str(uuid.uuid4()),
                    file_fk=file_record.id,
                    annotation_fk=annotation.id,
                    type=file_values["type"]
                ))

    def _create_file(self, session, values, now):
        file_record = File(
            id=str(uuid.uuid4()),
            path=values["path"],
            created_at=now,
            updated_at=now,
            file_metadata=values.get("metadata")
        )
        session.add(file_record)
        session.flush()
        return file_record
