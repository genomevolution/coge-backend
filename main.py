from fastapi import FastAPI, Response, UploadFile, File, Form, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from repository.db_config import DBConfig
from repository.db import DB
from controller.genome import GenomeController
from service.genome import GenomeService
from repository.genome import GenomeRepository
from repository.annotation import AnnotationRepository
from repository.file import FileRepository
from repository.processing_execution import ProcessingExecutionRepository
from service.minio_service import MinIOService
from service.genome_uploader_service import GenomeUploaderService
from service.annotation import AnnotationService
from service.annotation_uploader_service import AnnotationUploaderService
from service.nextflow_executor_service import NextflowExecutorService
from service.genome_processing_service import GenomeProcessingService
from service.genome_execution_monitor_service import GenomeExecutionMonitorService
from service.annotation_processing_service import AnnotationProcessingService
from service.annotation_execution_monitor_service import AnnotationExecutionMonitorService
from controller.annotation import AnnotationController
from controller.organism import OrganismController
from service.organism import OrganismService
from repository.organism import OrganismRepository
from controller.source import SourceController
from service.source import SourceService
from repository.source import SourceRepository
from controller.data_import import DataImportController
from repository.data_import import DataImportRepository
from repository.import_publisher import ImportPublisherRepository
from service.data_import import DataImportService
from service.import_coordinator import ImportCoordinatorService
from service.import_monitor_service import ImportMonitorService
from config import config

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan - start/stop background services"""
    await genome_monitor_service.start()
    await annotation_monitor_service.start()
    await import_monitor_service.start()
    yield
    await import_monitor_service.stop()
    await genome_monitor_service.stop()
    await annotation_monitor_service.stop()

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

db = DB(DBConfig())
minioService = MinIOService()
fileRepository = FileRepository(db)
processingExecutionRepository = ProcessingExecutionRepository(db)

nextflowExecutor = NextflowExecutorService(
    work_dir=config.NEXTFLOW_WORK_DIR,
    output_dir=config.NEXTFLOW_OUTPUT_DIR
)
genomeProcessingService = GenomeProcessingService(
    nextflowExecutor,
    minioService,
    processingExecutionRepository,
    fileRepository
)

annotationProcessingService = AnnotationProcessingService(
    nextflowExecutor,
    minioService,
    processingExecutionRepository,
    fileRepository
)

# Background monitor services - auto-finalize completed executions
genome_monitor_service = GenomeExecutionMonitorService(
    genomeProcessingService,
    processingExecutionRepository,
    check_interval_seconds=10  # Check every 10 seconds
)

annotation_monitor_service = AnnotationExecutionMonitorService(
    annotationProcessingService,
    processingExecutionRepository,
    check_interval_seconds=10  # Check every 10 seconds
)

genomeUploaderService = GenomeUploaderService(minioService, fileRepository)
annotationRepository = AnnotationRepository(db)
annotationUploaderService = AnnotationUploaderService(
    minioService,
    fileRepository,
    annotationRepository
)
annotationService = AnnotationService(annotationRepository, annotationUploaderService)
genomeService = GenomeService(GenomeRepository(db), genomeUploaderService)
genomeController = GenomeController(genomeService, minioService, genomeProcessingService)
organismController = OrganismController(OrganismService(OrganismRepository(db)))
annotationController = AnnotationController(annotationService, annotationProcessingService)
sourceController = SourceController(SourceService(SourceRepository(db)))
dataImportRepository = DataImportRepository(db)
importPublisherRepository = ImportPublisherRepository(db)
importCoordinatorService = ImportCoordinatorService(
    dataImportRepository,
    importPublisherRepository,
    minioService,
    nextflowExecutor
)
dataImportService = DataImportService(
    dataImportRepository,
    OrganismRepository(db),
    minioService,
    nextflowExecutor
)
dataImportController = DataImportController(dataImportService)
import_monitor_service = ImportMonitorService(
    dataImportRepository,
    importCoordinatorService,
    check_interval_seconds=2
)

@app.get("/organisms/")
def getOrganismsListAlchemy(response: Response, previous: str = None, next: str = None):
    response.headers["Content-Type"] = "application/json"
    return organismController.get_organisms(previous, next)

@app.get("/organisms/{organismId}")
def getOrganism(response: Response, organismId: str):
    response.headers["Content-Type"] = "application/json"
    return organismController.get_organism_by_id(organismId)

@app.get("/genomes/")
def getGenomes(response: Response, previous: str = None, next: str = None):
    response.headers["Content-Type"] = "application/json"
    return genomeController.get_genomes(previous, next)

@app.get("/genomes/{genomeId}")
def getGenomeById(response: Response, genomeId: str):
    response.headers["Content-Type"] = "application/json"
    return genomeController.get_genome_by_id(genomeId)

@app.get("/sources/")
def getSources(response: Response):
    response.headers["Content-Type"] = "application/json"
    return sourceController.get_sources()

@app.post("/imports/", status_code=202)
def createDataImport(
    payload: str = Form(...),
    fasta: UploadFile = File(None),
    gff3: UploadFile = File(None)
):
    return dataImportController.create_import(payload, fasta, gff3)

@app.get("/imports/")
def getActiveDataImports():
    return dataImportController.get_active_imports()

@app.get("/imports/{importId}")
def getDataImport(importId: str):
    return dataImportController.get_import(importId)

@app.put("/imports/{importId}/files/fasta")
def replaceImportFasta(importId: str, file: UploadFile = File(...)):
    return dataImportController.replace_fasta(importId, file)

@app.put("/imports/{importId}/files/gff3")
def replaceImportGff3(importId: str, file: UploadFile = File(...)):
    return dataImportController.replace_gff3(importId, file)

@app.delete("/imports/{importId}/annotation")
def removeImportAnnotation(importId: str):
    return dataImportController.remove_annotation(importId)

@app.post("/imports/{importId}/retry")
def retryDataImport(importId: str):
    return dataImportController.retry_import(importId)

@app.delete("/imports/{importId}")
def cancelDataImport(importId: str):
    return dataImportController.cancel_import(importId)

@app.get("/files/download")
def downloadFile(filePath: str):
    """Download a file from MinIO using its path"""
    try:
        file_data = genomeController.download_file(filePath)
        return StreamingResponse(
            file_data,
            media_type="application/octet-stream",
            headers={
                "Content-Disposition": f"attachment; filename={filePath.split('/')[-1]}"
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to download file: {str(e)}")

@app.get("/processing/executions/{executionId}")
def getProcessingExecutionStatus(response: Response, executionId: str):
    """Get the status of a genome processing execution (Nextflow pipeline)"""
    response.headers["Content-Type"] = "application/json"
    return genomeController.get_processing_execution_status(executionId)

@app.post("/processing/executions/{executionId}/finalize")
def finalizeProcessingExecution(response: Response, executionId: str):
    """Finalize a completed execution by uploading generated files to MinIO"""
    response.headers["Content-Type"] = "application/json"
    return genomeController.finalize_processing_execution(executionId)

@app.delete("/processing/executions/{executionId}")
def cancelProcessingExecution(response: Response, executionId: str):
    """Cancel a running genome processing execution"""
    response.headers["Content-Type"] = "application/json"
    return genomeController.cancel_processing_execution(executionId)

@app.get("/annotations/processing/executions/{executionId}")
def getAnnotationProcessingExecutionStatus(response: Response, executionId: str):
    """Get the status of an annotation processing execution (Nextflow pipeline)"""
    response.headers["Content-Type"] = "application/json"
    return annotationController.get_processing_execution_status(executionId)

@app.post("/annotations/processing/executions/{executionId}/finalize")
def finalizeAnnotationProcessingExecution(response: Response, executionId: str):
    """Finalize a completed annotation execution by uploading generated files to MinIO"""
    response.headers["Content-Type"] = "application/json"
    return annotationController.finalize_processing_execution(executionId)

@app.delete("/annotations/processing/executions/{executionId}")
def cancelAnnotationProcessingExecution(response: Response, executionId: str):
    """Cancel a running annotation processing execution"""
    response.headers["Content-Type"] = "application/json"
    return annotationController.cancel_processing_execution(executionId)
