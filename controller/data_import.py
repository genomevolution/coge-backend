from typing import Optional

from fastapi import File, HTTPException, UploadFile

from model.exceptions.entity_not_found import EntityNotFoundException
from model.exceptions.invalid_file_type import InvalidFileTypeException
from service.data_import import DataImportService


class DataImportController:
    def __init__(self, service: DataImportService):
        self.service = service

    def create_import(
        self,
        payload: str,
        fasta: Optional[UploadFile] = File(None),
        gff3: Optional[UploadFile] = File(None)
    ):
        return self._handle(
            lambda: self.service.create_import(payload, fasta, gff3)
        )

    def get_active_imports(self):
        return self.service.get_active_imports()

    def get_import(self, import_id: str):
        return self._handle(lambda: self.service.get_import(import_id))

    def replace_fasta(self, import_id: str, file: UploadFile):
        return self._handle(lambda: self.service.replace_fasta(import_id, file))

    def replace_gff3(self, import_id: str, file: UploadFile):
        return self._handle(lambda: self.service.replace_gff3(import_id, file))

    def remove_annotation(self, import_id: str):
        return self._handle(lambda: self.service.remove_annotation(import_id))

    def retry_import(self, import_id: str):
        return self._handle(lambda: self.service.retry_import(import_id))

    def cancel_import(self, import_id: str):
        return self._handle(lambda: self.service.cancel_import(import_id))

    def _handle(self, operation):
        try:
            return operation()
        except InvalidFileTypeException as error:
            raise HTTPException(status_code=400, detail=str(error)) from error
        except EntityNotFoundException as error:
            raise HTTPException(status_code=404, detail=str(error)) from error
        except ValueError as error:
            raise HTTPException(status_code=400, detail=str(error)) from error
        except Exception as error:
            raise HTTPException(status_code=500, detail=str(error)) from error
