from __future__ import annotations

import gzip
import json
import logging
import re
import shutil
import subprocess
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from config import config
from repository.blast import BlastRepository
from service.nextflow_executor_service import NextflowExecutorService
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from service.minio_service import MinIOService


logger = logging.getLogger(__name__)
FASTA_ALPHABET = re.compile(r"^[ACGTUNRYKMSWBDHV\-]+$", re.IGNORECASE)
BLAST_STATUSES = {"QUEUED", "PREPARING", "RUNNING", "COMPLETED", "FAILED", "EXPIRED"}


def utc_now() -> datetime:
    """Return a timezone-aware UTC timestamp for PostgreSQL timestamptz fields."""
    return datetime.now(timezone.utc)


class BlastService:
    def __init__(self, repository: BlastRepository):
        self.repository = repository

    def list_genomes(self, query: Optional[str], tax_id: Optional[str], limit: int, offset: int):
        limit = min(max(limit, 1), 100)
        offset = max(offset, 0)
        return self.repository.list_target_genomes(query, tax_id, limit, offset)

    def create_job(self, payload: Dict[str, Any]):
        program = payload.get("program", "blastn")
        if program != "blastn":
            raise ValueError("Only blastn is currently supported")

        query_fasta = self._normalize_query(payload.get("query", ""))
        selection = self._normalize_selection(payload.get("selection") or {})
        targets = self.repository.get_targets_for_selection(selection)
        if not targets:
            raise ValueError("Select at least one public genome with a FASTA file")
        if len(targets) > config.BLAST_MAX_TARGET_GENOMES:
            raise ValueError(
                f"The selection contains {len(targets)} genomes; the maximum is "
                f"{config.BLAST_MAX_TARGET_GENOMES}"
            )

        raw_parameters = payload.get("parameters") or {}
        evalue = self._parse_evalue(raw_parameters.get("evalue", 1e-5))
        max_target_seqs = self._parse_positive_int(
            raw_parameters.get("maxTargetSeqs", 50), "maxTargetSeqs", maximum=1000
        )
        job = self.repository.create_job(
            program=program,
            query_fasta=query_fasta,
            selection=selection,
            parameters={
                "evalue": evalue,
                "maxTargetSeqs": max_target_seqs,
                "targetCount": len(targets),
            },
            retention_hours=config.BLAST_RESULT_RETENTION_HOURS,
        )
        return job.to_dict()

    def get_job(self, job_id: str, include_results: bool = False):
        job = self.repository.get_job(job_id)
        if job is None:
            raise LookupError("BLAST job not found")
        if job.expires_at <= utc_now():
            raise LookupError("BLAST job has expired")
        return job.to_dict(include_results=include_results)

    def get_results_tsv(self, job_id: str) -> str:
        job = self.repository.get_job(job_id)
        if job is None:
            raise LookupError("BLAST job not found")
        if job.expires_at <= utc_now():
            raise LookupError("BLAST job has expired")
        columns = [
            "genome_id", "genome_name", "organism", "query_id", "sequence_id",
            "identity", "alignment_length", "query_start", "query_end",
            "subject_start", "subject_end", "evalue", "bit_score",
        ]
        lines = ["\t".join(columns)]
        for result in job.results or []:
            organism = (result.get("organism") or {}).get("speciesName") or ""
            lines.append("\t".join(str(value or "") for value in [
                result.get("genomeId"), result.get("genomeName"), organism,
                result.get("queryId"), result.get("sequenceId"), result.get("identity"),
                result.get("alignmentLength"), result.get("queryStart"), result.get("queryEnd"),
                result.get("subjectStart"), result.get("subjectEnd"), result.get("evalue"),
                result.get("bitScore"),
            ]))
        return "\n".join(lines) + "\n"

    def _normalize_query(self, query: str) -> str:
        value = str(query or "").strip()
        if not value:
            raise ValueError("A DNA sequence is required")
        lines = [line.strip() for line in value.splitlines() if line.strip()]
        if lines and lines[0].startswith(">"):
            if any(line.startswith(">") for line in lines[1:]):
                raise ValueError("Only one FASTA sequence can be searched at a time")
            sequence_lines = [line for line in lines[1:] if not line.startswith(">")]
            if not sequence_lines:
                raise ValueError("The FASTA query has no sequence")
            sequence = "".join(sequence_lines)
            fasta = value
        else:
            sequence = "".join(lines)
            fasta = ">query\n" + sequence
        if len(sequence) > config.BLAST_MAX_QUERY_LENGTH:
            raise ValueError(
                f"The query cannot exceed {config.BLAST_MAX_QUERY_LENGTH} bases"
            )
        if not FASTA_ALPHABET.fullmatch(sequence):
            raise ValueError("The query contains characters outside the IUPAC DNA alphabet")
        return fasta + ("\n" if not fasta.endswith("\n") else "")

    def _normalize_selection(self, selection: Dict[str, Any]):
        mode = selection.get("mode", "IDS").upper()
        if mode not in {"IDS", "FILTER"}:
            raise ValueError("selection.mode must be IDS or FILTER")
        genome_ids = list(dict.fromkeys(selection.get("genomeIds") or []))
        excluded = list(dict.fromkeys(selection.get("excludedGenomeIds") or []))
        if mode == "IDS" and not genome_ids:
            raise ValueError("At least one genomeId is required")
        return {
            "mode": mode,
            "genomeIds": genome_ids,
            "query": (selection.get("query") or "").strip() or None,
            "taxId": (selection.get("taxId") or "").strip() or None,
            "excludedGenomeIds": excluded,
        }

    def _parse_evalue(self, value):
        try:
            parsed = float(value)
        except (TypeError, ValueError) as error:
            raise ValueError("parameters.evalue must be a positive number") from error
        if parsed <= 0:
            raise ValueError("parameters.evalue must be a positive number")
        return parsed

    def _parse_positive_int(self, value, name: str, maximum: int):
        try:
            parsed = int(value)
        except (TypeError, ValueError) as error:
            raise ValueError(f"parameters.{name} must be an integer") from error
        if parsed < 1 or parsed > maximum:
            raise ValueError(f"parameters.{name} must be between 1 and {maximum}")
        return parsed


class BlastCoordinatorService:
    def __init__(
        self,
        repository: BlastRepository,
        minio_service: MinIOService,
        nextflow_executor: NextflowExecutorService,
    ):
        self.repository = repository
        self.minio_service = minio_service
        self.nextflow_executor = nextflow_executor
        self.jobs_root = Path(config.BLAST_JOBS_DIR)
        self.database_root = Path(config.BLAST_DATABASE_DIR)
        self.jobs_root.mkdir(parents=True, exist_ok=True)
        self.database_root.mkdir(parents=True, exist_ok=True)
        self._database_locks: dict[str, threading.Lock] = {}

    def process_job(self, job_id: str):
        job = self.repository.get_job(job_id)
        if job is None:
            return
        job_dir = self.jobs_root / job_id
        execution_id = None
        try:
            targets = self.repository.get_targets_for_selection(job.selection)
            if not targets:
                raise ValueError("No genomes matched the selection")
            self.repository.update_job(job_id, status="PREPARING", progress=10)
            manifest_path = self._prepare_databases(job_id, job_dir, targets)
            query_path = job_dir / "query.fasta"
            query_path.write_text(job.query_fasta, encoding="utf-8")
            output_dir = job_dir / "output"
            execution_id = self.nextflow_executor.execute_blast_search(
                job_id=job_id,
                query_local_path=str(query_path),
                database_manifest_path=str(manifest_path),
                output_dir=str(output_dir),
                max_target_seqs=job.parameters.get("maxTargetSeqs", 50),
                evalue=job.parameters.get("evalue", 1e-5),
            )
            self.repository.update_job(
                job_id,
                status="RUNNING",
                progress=20,
                execution_id=execution_id,
            )
            status = self._wait_for_execution(execution_id)
            if status.get("status") != "COMPLETED":
                raise RuntimeError(status.get("error_message") or "BLAST execution failed")
            results_file = Path(status["output_dir"]) / "blast_results.tsv"
            results = self._parse_results(results_file, targets)
            self.repository.update_job(
                job_id,
                status="COMPLETED",
                progress=100,
                result_count=len(results),
                results=results,
                completed_at=utc_now(),
                error_message=None,
            )
        except Exception as error:
            logger.exception("BLAST job %s failed", job_id)
            self.repository.update_job(
                job_id,
                status="FAILED",
                progress=100,
                completed_at=utc_now(),
                error_message=str(error),
            )
        finally:
            if execution_id:
                self.nextflow_executor.cleanup_execution(execution_id)
            shutil.rmtree(job_dir, ignore_errors=True)

    def _prepare_databases(self, job_id: str, job_dir: Path, targets):
        job_dir.mkdir(parents=True, exist_ok=True)
        manifest_path = job_dir / "databases.tsv"
        lines = []
        for index, target in enumerate(targets, start=1):
            database_prefix = self.database_root / target["id"] / target["id"]
            ready_marker = database_prefix.parent / ".ready"
            lock = self._database_locks.setdefault(target["id"], threading.Lock())
            with lock:
                if not ready_marker.exists():
                    genome_dir = database_prefix.parent
                    genome_dir.mkdir(parents=True, exist_ok=True)
                    fasta_path = job_dir / f"{target['id']}.fa"
                    self._download_fasta(target["fastaPath"], fasta_path)
                    subprocess.run(
                        [
                            "makeblastdb",
                            "-in", str(fasta_path),
                            "-dbtype", "nucl",
                            "-parse_seqids",
                            "-out", str(database_prefix),
                        ],
                        check=True,
                        capture_output=True,
                        text=True,
                    )
                    ready_marker.write_text("ready\n", encoding="utf-8")
            lines.append(f"{target['id']}\t{database_prefix}")
            progress = 10 + int(index / max(len(targets), 1) * 10)
            self.repository.update_job(job_id, progress=progress)
        manifest_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return manifest_path

    def _download_fasta(self, minio_path: str, local_path: Path):
        response = self.minio_service.download_file(minio_path)
        try:
            if minio_path.lower().endswith(".gz"):
                with gzip.GzipFile(fileobj=response, mode="rb") as compressed, local_path.open("wb") as output:
                    shutil.copyfileobj(compressed, output)
            else:
                with local_path.open("wb") as output:
                    for chunk in response.stream(amt=8 * 1024 * 1024):
                        output.write(chunk)
        finally:
            response.close()
            response.release_conn()

    def _wait_for_execution(self, execution_id: str):
        deadline = time.monotonic() + 60 * 60 * 24
        while time.monotonic() < deadline:
            status = self.nextflow_executor.get_execution_status(execution_id)
            if status.get("status") != "RUNNING":
                return status
            time.sleep(2)
        self.nextflow_executor.cancel_execution(execution_id)
        return {"status": "FAILED", "error_message": "BLAST execution exceeded 24 hours"}

    def _parse_results(self, result_path: Path, targets):
        target_by_id = {target["id"]: target for target in targets}
        results = []
        if not result_path.exists():
            return results
        for line in result_path.read_text(encoding="utf-8").splitlines():
            columns = line.split("\t")
            if len(columns) < 17:
                continue
            genome_id = columns[0]
            target = target_by_id.get(genome_id, {})
            results.append({
                "genomeId": genome_id,
                "genomeName": target.get("name"),
                "organism": target.get("organism"),
                "queryId": columns[1],
                "sequenceId": columns[2],
                "identity": float(columns[3]),
                "alignmentLength": int(columns[4]),
                "queryStart": int(columns[7]),
                "queryEnd": int(columns[8]),
                "subjectStart": int(columns[9]),
                "subjectEnd": int(columns[10]),
                "evalue": float(columns[11]),
                "bitScore": float(columns[12]),
                "queryLength": int(columns[13]),
                "subjectLength": int(columns[14]),
                "querySequence": columns[15][:10000],
                "subjectSequence": columns[16][:10000],
            })
        return results
