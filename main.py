from typing import Union
from fastapi import FastAPI, Response, UploadFile, File, HTTPException
from fastapi.responses import StreamingResponse
from repository.dbConfig import DBConfig
from repository.db import DB

from controller.genome import GenomeController
from service.genome import GenomeService
from repository.genome import GenomeRepository

from repository.annotation import AnnotationRepository

from repository.file import FileRepository
from service.minioService import MinIOService
from service.genomeUploaderService import GenomeUploaderService
from service.annotationUploaderService import AnnotationUploaderService

from controller.biosample import BiosampleController
from service.biosample import BiosampleService
from repository.biosample import BiosampleRepository

app = FastAPI()

db = DB(DBConfig())
minioService = MinIOService()
fileRepository = FileRepository(db)
genomeUploaderService = GenomeUploaderService(minioService, fileRepository)
annotationUploaderService = AnnotationUploaderService(minioService, fileRepository, AnnotationRepository(db))
genomeService = GenomeService(GenomeRepository(db), genomeUploaderService, annotationUploaderService)
genomeController = GenomeController(genomeService, minioService)
biosampleController = BiosampleController(BiosampleService(BiosampleRepository(db)))

@app.get("/biosamples/")
def getBiosamplesList(response: Response, previous: str = None, next: str = None):
    response.headers["Content-Type"] = "application/json"
    response.headers["Access-Control-Allow-Origin"] = "http://localhost:3000"
    return biosampleController.getBiosamplesList(previous, next)

@app.get("/biosamples/{biosamplesId}")
def getBiosample(response: Response, biosamplesId: str):
    response.headers["Content-Type"] = "application/json"
    response.headers["Access-Control-Allow-Origin"] = "http://localhost:3000"
    return biosampleController.getBiosample(biosamplesId)

@app.get("/genomes/")
def getGenomesList(response: Response, previous: str = None, next: str = None):
    response.headers["Content-Type"] = "application/json"
    response.headers["Access-Control-Allow-Origin"] = "http://localhost:3000"
    return genomeController.getGenomesList(previous, next)

@app.get("/genomes/{genomeId}")
def getGenome(response: Response, genomeId: str):
    response.headers["Content-Type"] = "application/json"
    response.headers["Access-Control-Allow-Origin"] = "http://localhost:3000"
    return genomeController.getGenome(genomeId)

# File upload endpoints
@app.post("/biosamples/{biosampleId}/genomes/{genomeId}/upload")
def uploadGenomeFile(response: Response, biosampleId: str, genomeId: str, file: UploadFile = File(...)):
    """Upload a genome file (.fa, .fasta, .fna) for a specific genome"""
    response.headers["Access-Control-Allow-Origin"] = "http://localhost:3000"
    return genomeController.uploadGenomeFile(biosampleId, genomeId, file)

@app.post("/genomes/{genomeId}/annotations/{annotationId}/upload")
def uploadAnnotationFile(response: Response, genomeId: str, annotationId: str, file: UploadFile = File(...)):
    """Upload an annotation file (.gff3, .gff) for a specific genome"""
    response.headers["Access-Control-Allow-Origin"] = "http://localhost:3000"
    return genomeController.uploadAnnotationFile(genomeId, annotationId, file)

@app.get("/files/download")
def downloadFile(response: Response, filePath: str):
    """Download a file from MinIO using its path"""
    try:
        file_data = genomeController.downloadFile(filePath)
        return StreamingResponse(
            file_data,
            media_type="application/octet-stream",
            headers={
                "Content-Disposition": f"attachment; filename={filePath.split('/')[-1]}",
                "Access-Control-Allow-Origin": "http://localhost:3000"
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to download file: {str(e)}")

@app.delete("/files/delete")
def deleteFile(response: Response, filePath: str):
    """Delete a file from MinIO using its path"""
    response.headers["Access-Control-Allow-Origin"] = "http://localhost:3000"
    return genomeController.deleteFile(filePath)
