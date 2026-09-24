from fastapi import HTTPException

from model.exceptions.entity_not_found import EntityNotFoundException
from service.taxonomy import TaxonomyService


class TaxonomyController:
    def __init__(self, service: TaxonomyService):
        self.service = service

    def get_by_tax_id(self, tax_id: str):
        try:
            return self.service.get_by_tax_id(tax_id)
        except EntityNotFoundException as error:
            raise HTTPException(status_code=404, detail=str(error)) from error
        except ValueError as error:
            raise HTTPException(status_code=400, detail=str(error)) from error
        except Exception as error:
            raise HTTPException(
                status_code=500,
                detail=f"Internal server error: {error}"
            ) from error

    def search(self, query: str, limit: int):
        try:
            return self.service.search(query, limit)
        except ValueError as error:
            raise HTTPException(status_code=400, detail=str(error)) from error
        except Exception as error:
            raise HTTPException(
                status_code=500,
                detail=f"Internal server error: {error}"
            ) from error
