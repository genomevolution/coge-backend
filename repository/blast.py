from datetime import datetime, timedelta, timezone
import uuid
from typing import Any, Dict, Optional

from sqlalchemy import and_, desc, func, or_
from sqlalchemy.orm import joinedload

from model import BlastJob, File, Genome, GenomeFile, Organism
from repository.db import DB


FASTA_FILE_TYPE = "FASTA_GZ"
ACTIVE_JOB_STATUSES = ("QUEUED", "PREPARING", "RUNNING")


def utc_now() -> datetime:
    """Return a timezone-aware UTC timestamp for PostgreSQL timestamptz fields."""
    return datetime.now(timezone.utc)


class BlastRepository:
    def __init__(self, db: DB):
        self.db = db

    def list_target_genomes(
        self,
        query: Optional[str],
        tax_id: Optional[str],
        limit: int,
        offset: int,
    ) -> Dict[str, Any]:
        session = self.db.get_session()
        try:
            base = self._target_genome_query(session, query, tax_id, load_files=False)
            total = base.with_entities(func.count(func.distinct(Genome.id))).scalar() or 0
            genomes = (
            self._target_genome_query(session, query, tax_id, load_files=True)
                .order_by(desc(Genome.created_at), Genome.id)
                .offset(offset)
                .limit(limit)
                .all()
            )
            return {
                "items": [self._target_to_dict(genome) for genome in genomes],
                "total": total,
                "limit": limit,
                "offset": offset,
            }
        finally:
            session.close()

    def get_targets_for_selection(self, selection: Dict[str, Any]):
        session = self.db.get_session()
        try:
            query = self._target_genome_query(
                session,
                selection.get("query"),
                selection.get("taxId"),
                load_files=True,
            )
            mode = selection.get("mode", "IDS")
            if mode == "IDS":
                ids = selection.get("genomeIds", [])
                query = query.filter(Genome.id.in_(ids)) if ids else query.filter(False)
            elif selection.get("genomeIds"):
                query = query.filter(Genome.id.in_(selection["genomeIds"]))

            excluded = selection.get("excludedGenomeIds", [])
            if excluded:
                query = query.filter(~Genome.id.in_(excluded))

            return [self._target_to_dict(genome) for genome in query.order_by(Genome.id).all()]
        finally:
            session.close()

    def create_job(
        self,
        program: str,
        query_fasta: str,
        selection: Dict[str, Any],
        parameters: Dict[str, Any],
        retention_hours: int,
    ) -> BlastJob:
        now = utc_now()
        session = self.db.get_session()
        try:
            job = BlastJob(
                id=str(uuid.uuid4()),
                program=program,
                status="QUEUED",
                progress=0,
                query_fasta=query_fasta,
                selection=selection,
                parameters=parameters,
                created_at=now,
                expires_at=now + timedelta(hours=retention_hours),
            )
            session.add(job)
            session.commit()
            session.refresh(job)
            return job
        finally:
            session.close()

    def get_job(self, job_id: str) -> Optional[BlastJob]:
        session = self.db.get_session()
        try:
            job = session.query(BlastJob).filter(BlastJob.id == job_id).first()
            if job is None:
                return None
            session.expunge(job)
            return job
        finally:
            session.close()

    def claim_next_job(self) -> Optional[str]:
        session = self.db.get_session()
        try:
            job = (
                session.query(BlastJob)
                .filter(BlastJob.status == "QUEUED", BlastJob.expires_at > utc_now())
                .order_by(BlastJob.created_at)
                .with_for_update(skip_locked=True)
                .first()
            )
            if job is None:
                return None
            job.status = "PREPARING"
            job.started_at = utc_now()
            job.progress = 5
            session.commit()
            return job.id
        finally:
            session.close()

    def update_job(self, job_id: str, **values) -> Optional[BlastJob]:
        session = self.db.get_session()
        try:
            job = session.query(BlastJob).filter(BlastJob.id == job_id).first()
            if job is None:
                return None
            for key, value in values.items():
                setattr(job, key, value)
            session.commit()
            session.refresh(job)
            session.expunge(job)
            return job
        finally:
            session.close()

    def delete_expired_jobs(self):
        session = self.db.get_session()
        try:
            jobs = session.query(BlastJob).filter(
                BlastJob.expires_at <= utc_now(),
                ~BlastJob.status.in_(ACTIVE_JOB_STATUSES),
            ).all()
            ids = [job.id for job in jobs]
            for job in jobs:
                session.delete(job)
            session.commit()
            return ids
        finally:
            session.close()

    def _target_genome_query(self, session, query: Optional[str], tax_id: Optional[str], load_files: bool = True):
        statement = (
            session.query(Genome)
            .join(Organism, Genome.organism_fk == Organism.id)
            .join(GenomeFile, GenomeFile.genome_fk == Genome.id)
            .join(File, File.id == GenomeFile.file_fk)
            .filter(Genome.public.is_(True), GenomeFile.type == FASTA_FILE_TYPE)
        )
        if load_files:
            statement = statement.options(
                joinedload(Genome.organism),
                joinedload(Genome.genome_files).joinedload(GenomeFile.file),
            )
        if query:
            pattern = f"%{query.strip()}%"
            statement = statement.filter(
                or_(
                    Genome.name.ilike(pattern),
                    Genome.accesion_id.ilike(pattern),
                    Organism.name.ilike(pattern),
                    Organism.species_name.ilike(pattern),
                    Organism.tax_id.ilike(pattern),
                )
            )
        if tax_id:
            statement = statement.filter(Organism.tax_id == tax_id.strip())
        return statement.distinct()

    def _target_to_dict(self, genome: Genome) -> Dict[str, Any]:
        fasta_file = next(
            (
                link.file.path
                for link in genome.genome_files
                if link.type == FASTA_FILE_TYPE and link.file is not None
            ),
            None,
        )
        return {
            "id": genome.id,
            "name": genome.name,
            "accessionId": genome.accesion_id,
            "organism": {
                "id": genome.organism.id,
                "name": genome.organism.name,
                "speciesName": genome.organism.species_name,
                "taxId": genome.organism.tax_id,
            },
            "fastaPath": fasta_file,
        }
