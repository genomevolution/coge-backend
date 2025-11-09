from fastapi import FastAPI, Response, UploadFile, File, HTTPException
from fastapi.responses import StreamingResponse
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
from service.nextflow_executor_service import NextflowExecutorService
from service.genome_processing_service import GenomeProcessingService
from service.genome_execution_monitor_service import GenomeExecutionMonitorService
from service.annotation_processing_service import AnnotationProcessingService
from service.annotation_execution_monitor_service import AnnotationExecutionMonitorService
from controller.annotation import AnnotationController
from controller.organism import OrganismController
from service.organism import OrganismService
from repository.organism import OrganismRepository
from config import config

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan - start/stop background services"""
    await genome_monitor_service.start()
    await annotation_monitor_service.start()
    yield
    await genome_monitor_service.stop()
    await annotation_monitor_service.stop()

app = FastAPI(lifespan=lifespan)

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
annotationService = AnnotationService(minioService, fileRepository, AnnotationRepository(db))
genomeService = GenomeService(GenomeRepository(db), genomeUploaderService)
genomeController = GenomeController(genomeService, minioService, genomeProcessingService)
organismController = OrganismController(OrganismService(OrganismRepository(db)))
annotationController = AnnotationController(annotationService, annotationProcessingService)

@app.get("/organisms/")
def getOrganismsListAlchemy(response: Response, previous: str = None, next: str = None):
    response.headers["Content-Type"] = "application/json"
    response.headers["Access-Control-Allow-Origin"] = "http://localhost:3000"
    return organismController.get_organisms(previous, next)

@app.get("/organisms/{organismId}")
def getOrganism(response: Response, organismId: str):
    response.headers["Content-Type"] = "application/json"
    response.headers["Access-Control-Allow-Origin"] = "http://localhost:3000"
    return organismController.get_organism_by_id(organismId)

@app.get("/genomes/")
def getGenomes(response: Response, previous: str = None, next: str = None):
    response.headers["Content-Type"] = "application/json"
    response.headers["Access-Control-Allow-Origin"] = "http://localhost:3000"
    return genomeController.get_genomes(previous, next)

@app.get("/genomes/{genomeId}")
def getGenomeById(response: Response, genomeId: str):
    response.headers["Content-Type"] = "application/json"
    response.headers["Access-Control-Allow-Origin"] = "http://localhost:3000"
    return genomeController.get_genome_by_id(genomeId)

@app.post("/organisms/{organismId}/genomes/{genomeId}/upload")
def uploadGenomeFile(response: Response, organismId: str, genomeId: str, file: UploadFile = File(...)):
    """Upload a genome file (.fa, .fasta, .fna) and automatically start indexing for JBrowse"""
    response.headers["Access-Control-Allow-Origin"] = "http://localhost:3000"
    return genomeController.upload_genome_file(organismId, genomeId, file)

@app.post("/organisms/{organismId}/genomes/{genomeId}/annotations/{annotationId}/upload")
def uploadAnnotationFile(response: Response, organismId: str, genomeId: str, annotationId: str, file: UploadFile = File(...)):
    """Upload an annotation file (.gff3, .gff) and automatically start processing for JBrowse"""
    response.headers["Access-Control-Allow-Origin"] = "http://localhost:3000"
    return annotationController.upload_annotation_file(organismId, genomeId, annotationId, file)

@app.get("/files/download")
def downloadFile(response: Response, filePath: str):
    """Download a file from MinIO using its path"""
    try:
        file_data = genomeController.download_file(filePath)
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

@app.get("/processing/executions/{executionId}")
def getProcessingExecutionStatus(response: Response, executionId: str):
    """Get the status of a genome processing execution (Nextflow pipeline)"""
    response.headers["Content-Type"] = "application/json"
    response.headers["Access-Control-Allow-Origin"] = "http://localhost:3000"
    return genomeController.get_processing_execution_status(executionId)

@app.post("/processing/executions/{executionId}/finalize")
def finalizeProcessingExecution(response: Response, executionId: str):
    """Finalize a completed execution by uploading generated files to MinIO"""
    response.headers["Content-Type"] = "application/json"
    response.headers["Access-Control-Allow-Origin"] = "http://localhost:3000"
    return genomeController.finalize_processing_execution(executionId)

@app.delete("/processing/executions/{executionId}")
def cancelProcessingExecution(response: Response, executionId: str):
    """Cancel a running genome processing execution"""
    response.headers["Content-Type"] = "application/json"
    response.headers["Access-Control-Allow-Origin"] = "http://localhost:3000"
    return genomeController.cancel_processing_execution(executionId)

@app.get("/annotations/processing/executions/{executionId}")
def getAnnotationProcessingExecutionStatus(response: Response, executionId: str):
    """Get the status of an annotation processing execution (Nextflow pipeline)"""
    response.headers["Content-Type"] = "application/json"
    response.headers["Access-Control-Allow-Origin"] = "http://localhost:3000"
    return annotationController.get_processing_execution_status(executionId)

@app.post("/annotations/processing/executions/{executionId}/finalize")
def finalizeAnnotationProcessingExecution(response: Response, executionId: str):
    """Finalize a completed annotation execution by uploading generated files to MinIO"""
    response.headers["Content-Type"] = "application/json"
    response.headers["Access-Control-Allow-Origin"] = "http://localhost:3000"
    return annotationController.finalize_processing_execution(executionId)

@app.delete("/annotations/processing/executions/{executionId}")
def cancelAnnotationProcessingExecution(response: Response, executionId: str):
    """Cancel a running annotation processing execution"""
    response.headers["Content-Type"] = "application/json"
    response.headers["Access-Control-Allow-Origin"] = "http://localhost:3000"
    return annotationController.cancel_processing_execution(executionId)
