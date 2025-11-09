import os
import logging
from pathlib import Path
from typing import Dict
from datetime import datetime
from service.nextflow_executor_service import NextflowExecutorService
from service.minio_service import MinIOService
from repository.processing_execution import ProcessingExecutionRepository
from repository.file import FileRepository
from config import config
from service.execution_status import ExecutionStatus, ExecutionType

logger = logging.getLogger(__name__)

ANNOTATION_FILE_TYPE_MAPPING = {
    "sorted_gff3": "GFF3_SORTED",
    "gff3_gz": "GFF3_GZ",
    "tabix_index": "TABIX"
}

CONTENT_TYPE_MAPPING = {
    "sorted_gff3": "text/plain",
    "gff3_gz": "application/gzip",
    "tabix_index": "application/octet-stream"
}

DOWNLOAD_CHUNK_SIZE_BYTES = 8 * 1024 * 1024
UNKNOWN_FILE_TYPE = "UNKNOWN"
DEFAULT_CONTENT_TYPE = "application/octet-stream"

class AnnotationProcessingService:
    def __init__(
        self,
        nextflow_executor: NextflowExecutorService,
        minio_service: MinIOService,
        processing_execution_repo: ProcessingExecutionRepository,
        file_repository: FileRepository
    ):
        self.nextflow_executor = nextflow_executor
        self.minio_service = minio_service
        self.processing_execution_repo = processing_execution_repo
        self.file_repository = file_repository
        self.temp_dir = Path(config.PROCESSING_TEMP_DIR)
        self.temp_dir.mkdir(parents=True, exist_ok=True)
    
    def start_annotation_processing(
        self,
        organism_id: str,
        genome_id: str,
        annotation_id: str,
        gff3_minio_path: str,
        profile: str = "standard"
    ) -> str:
        temp_gff3 = self._get_temp_gff3_path(annotation_id)
        
        try:
            self._download_gff3_file(gff3_minio_path, temp_gff3)
            
            execution_id = self.nextflow_executor.execute_annotation_processing(
                organism_id=organism_id,
                genome_id=genome_id,
                annotation_id=annotation_id,
                gff3_local_path=temp_gff3,
                profile=profile
            )
            
            status = self.nextflow_executor.get_execution_status(execution_id)
            
            now = datetime.utcnow()
            self.processing_execution_repo.create_execution(
                execution_id=execution_id,
                genome_id=genome_id,
                execution_type=ExecutionType.ANNOTATION_PROCESSING,
                status=ExecutionStatus.RUNNING,
                progress=0,
                pid=status.get('pid'),
                profile=profile,
                original_path=gff3_minio_path,
                output_dir=status.get('output_dir'),
                log_file=status.get('log_file'),
                started_at=now,
                created_at=now,
                updated_at=now,
                metadata=self._create_execution_metadata(organism_id, annotation_id, temp_gff3)
            )
            
            return execution_id
            
        except Exception as e:
            if Path(temp_gff3).exists():
                Path(temp_gff3).unlink()
            raise e
    
    def finalize_execution(self, execution_id: str) -> Dict:
        logger.info(f"Starting finalization for annotation execution {execution_id}")
        
        status, db_execution = self._validate_execution_for_finalization(execution_id)
        
        generated_files = status.get('generated_files', {})
        logger.info(f"Generated files for execution {execution_id}: {generated_files}")
        
        organism_id = db_execution.execution_metadata.get('organism_id')
        genome_id = db_execution.genome_id
        annotation_id = db_execution.execution_metadata.get('annotation_id')
        
        logger.info(f"Processing files for annotation_id={annotation_id}, genome_id={genome_id}, organism_id={organism_id}")
        
        uploaded_files = self._process_and_upload_generated_files(
            generated_files, 
            organism_id, 
            genome_id,
            annotation_id,
            execution_id
        )
        
        logger.info(f"Successfully uploaded {len(uploaded_files)} files for execution {execution_id}")
        
        temp_gff3_path = db_execution.execution_metadata.get('temp_gff3_path', '')
        if temp_gff3_path and Path(temp_gff3_path).exists():
            Path(temp_gff3_path).unlink()
        
        self.processing_execution_repo.update_execution_metadata(
            execution_id,
            {"uploaded_files": uploaded_files},
            datetime.utcnow()
        )
        
        return {
            "execution_id": execution_id,
            "status": ExecutionStatus.FINALIZED,
            "uploaded_files": uploaded_files
        }
    
    def get_execution_status(self, execution_id: str) -> Dict:
        return self.nextflow_executor.get_execution_status(execution_id)
    
    def cancel_execution(self, execution_id: str) -> bool:
        cancelled = self.nextflow_executor.cancel_execution(execution_id)
        
        if cancelled:
            now = datetime.utcnow()
            self.processing_execution_repo.update_execution_status(
                execution_id,
                status=ExecutionStatus.CANCELLED,
                updated_at=now,
                completed_at=now
            )
        
        return cancelled
    
    def _validate_execution_for_finalization(self, execution_id: str):
        status = self.nextflow_executor.get_execution_status(execution_id)
        
        if status.get('status') != ExecutionStatus.COMPLETED:
            raise ValueError(f"Execution {execution_id} is not completed. Status: {status.get('status')}")
        
        db_execution = self.processing_execution_repo.get_execution_by_id(execution_id)
        if not db_execution:
            raise ValueError(f"Execution {execution_id} not found in database")
        
        return status, db_execution
    
    def _process_and_upload_generated_files(
        self, 
        generated_files: Dict, 
        organism_id: str, 
        genome_id: str,
        annotation_id: str,
        execution_id: str
    ) -> Dict:
        uploaded_files = {}
        
        logger.info(f"Processing {len(generated_files)} generated files")
        
        for file_type, local_path in generated_files.items():
            logger.info(f"Processing file_type={file_type}, local_path={local_path}")
            
            if local_path and Path(local_path).exists():
                logger.info(f"File exists: {local_path}")
                file_name = Path(local_path).name
                minio_path = f"annotation/{annotation_id}/{file_name}"
                
                with open(local_path, 'rb') as f:
                    file_size = os.path.getsize(local_path)
                    content_type = self._get_content_type(file_type)
                    self.minio_service.upload_file(f, minio_path, content_type, file_size)
                
                file_metadata = {
                    "original_filename": file_name,
                    "file_size": file_size,
                    "content_type": content_type,
                    "organism_id": organism_id,
                    "genome_id": genome_id,
                    "annotation_id": annotation_id,
                    "generated": True,
                    "execution_id": execution_id
                }
                
                file_record = self.file_repository.create_file(minio_path, file_metadata)
                
                annotation_file_type = self._get_annotation_file_type(file_type)
                annotation_file_link = self.file_repository.create_annotation_file_link(
                    file_record.id,
                    annotation_id,
                    annotation_file_type
                )
                
                if not annotation_file_link:
                    logger.error(f"Failed to create annotation file link for {file_type}")
                    raise ValueError(f"Failed to create annotation file link for {file_type}")
                
                logger.info(f"Successfully created annotation_file link: {annotation_file_link.id} for file_type={file_type}")
                
                uploaded_files[file_type] = {
                    "path": minio_path,
                    "file_id": file_record.id,
                    "annotation_file_link_id": annotation_file_link.id,
                    "url": self.minio_service.get_file_url(minio_path)
                }
            else:
                logger.warning(f"File does not exist or path is None: {local_path}")
        
        return uploaded_files
    
    def _download_gff3_file(self, minio_path: str, local_path: str) -> None:
        gff3_data = self.minio_service.download_file(minio_path)
        with open(local_path, 'wb') as f:
            for chunk in gff3_data.stream(amt=DOWNLOAD_CHUNK_SIZE_BYTES):
                f.write(chunk)
    
    def _get_temp_gff3_path(self, annotation_id: str) -> str:
        return str(self.temp_dir / f"{annotation_id}.gff3")
    
    def _create_execution_metadata(self, organism_id: str, annotation_id: str, temp_gff3_path: str) -> Dict:
        return {
            'organism_id': organism_id,
            'annotation_id': annotation_id,
            'temp_gff3_path': temp_gff3_path
        }
    
    def _get_content_type(self, file_type: str) -> str:
        return CONTENT_TYPE_MAPPING.get(file_type, DEFAULT_CONTENT_TYPE)
    
    def _get_annotation_file_type(self, file_type: str) -> str:
        return ANNOTATION_FILE_TYPE_MAPPING.get(file_type, UNKNOWN_FILE_TYPE)

