from typing import Optional

from fastapi import HTTPException

from service.blast import BlastService


class BlastController:
    def __init__(self, service: BlastService):
        self.service = service

    def list_genomes(self, query: Optional[str], tax_id: Optional[str], limit: int, offset: int):
        return self.service.list_genomes(query, tax_id, limit, offset)

    def create_job(self, payload: dict):
        try:
            return self.service.create_job(payload)
        except ValueError as error:
            raise HTTPException(status_code=400, detail=str(error)) from error

    def get_job(self, job_id: str, include_results: bool = False):
        try:
            return self.service.get_job(job_id, include_results=include_results)
        except LookupError as error:
            raise HTTPException(status_code=404, detail=str(error)) from error

    def get_results_tsv(self, job_id: str):
        try:
            return self.service.get_results_tsv(job_id)
        except LookupError as error:
            raise HTTPException(status_code=404, detail=str(error)) from error
