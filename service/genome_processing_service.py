import os
from pathlib import Path
from typing import Dict
from datetime import datetime
from service.nextflow_executor_service import NextflowExecutorService
from service.minio_service import MinIOService
from repository.processing_execution import ProcessingExecutionRepository
from repository.file import FileRepository
from config import config
from service.execution_status import ExecutionStatus, ExecutionType

GENOME_FILE_TYPE_MAPPING = {
    "fasta_gz": "FASTA_GZ",
    "gzi_index": "GZI",
    "fai_index": "FAI"
}

CONTENT_TYPE_MAPPING = {
    "fasta_gz": "application/gzip",
    "gzi_index": "application/octet-stream",
    "fai_index": "text/plain"
}

DOWNLOAD_CHUNK_SIZE_BYTES = 8 * 1024 * 1024
UNKNOWN_FILE_TYPE = "UNKNOWN"
DEFAULT_CONTENT_TYPE = "application/octet-stream"

class GenomeProcessingService:
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
    
    def start_genome_indexing(
        self,
        organism_id: str,
        genome_id: str,
        fasta_minio_path: str,
        profile: str = "standard"
    ) -> str:
        temp_fasta = self._get_temp_fasta_path(genome_id)
        
        try:
            self._download_fasta_file(fasta_minio_path, temp_fasta)
            
            execution_id = self.nextflow_executor.execute_genome_indexing(
                organism_id=organism_id,
                genome_id=genome_id,
                fasta_local_path=temp_fasta,
                profile=profile
            )
            
            status = self.nextflow_executor.get_execution_status(execution_id)
            
            now = datetime.utcnow()
            self.processing_execution_repo.create_execution(
                execution_id=execution_id,
                genome_id=genome_id,
                execution_type=ExecutionType.GENOME_INDEXING,
                status=ExecutionStatus.RUNNING,
                progress=0,
                pid=status.get('pid'),
                profile=profile,
                original_path=fasta_minio_path,
                output_dir=status.get('output_dir'),
                log_file=status.get('log_file'),
                started_at=now,
                created_at=now,
                updated_at=now,
                metadata=self._create_execution_metadata(organism_id, temp_fasta)
            )
            
            return execution_id
            
        except Exception as e:
            if Path(temp_fasta).exists():
                Path(temp_fasta).unlink()
            raise e
    
    def finalize_execution(self, execution_id: str) -> Dict:
        status, db_execution = self._validate_execution_for_finalization(execution_id)
        
        generated_files = status.get('generated_files', {})
        organism_id = db_execution.execution_metadata.get('organism_id')
        genome_id = db_execution.genome_id
        
        uploaded_files = self._process_and_upload_generated_files(
            generated_files, 
            organism_id, 
            genome_id, 
            execution_id
        )
        
        temp_fasta_path = db_execution.execution_metadata.get('temp_fasta_path', '')
        if temp_fasta_path and Path(temp_fasta_path).exists():
            Path(temp_fasta_path).unlink()
        
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
        execution_id: str
    ) -> Dict:
        uploaded_files = {}
        
        for file_type, local_path in generated_files.items():
            if local_path and Path(local_path).exists():
                file_name = Path(local_path).name
                minio_path = f"{organism_id}/genomes/{file_name}"
                
                with open(local_path, 'rb') as f:
                    file_size = os.path.getsize(local_path)
                    content_type = self._get_content_type(file_type)
                    self.minio_service.upload_file(f, minio_path, content_type, file_size)
                
                file_metadata = {
                    "original_filename": file_name,
                    "file_size": file_size,
                    "content_type": content_type,
                    "organism_id": organism_id,
                    "generated": True,
                    "execution_id": execution_id
                }
                
                file_record = self.file_repository.create_file(minio_path, file_metadata)
                
                genome_file_type = self._get_genome_file_type(file_type)
                self.file_repository.create_genome_file_link(
                    file_record.id,
                    genome_id,
                    genome_file_type
                )
                
                uploaded_files[file_type] = {
                    "path": minio_path,
                    "file_id": file_record.id,
                    "url": self.minio_service.get_file_url(minio_path)
                }
        
        return uploaded_files
    
    def _download_fasta_file(self, minio_path: str, local_path: str) -> None:
        fasta_data = self.minio_service.download_file(minio_path)
        with open(local_path, 'wb') as f:
            for chunk in fasta_data.stream(amt=DOWNLOAD_CHUNK_SIZE_BYTES):
                f.write(chunk)
    
    def _get_temp_fasta_path(self, genome_id: str) -> str:
        return str(self.temp_dir / f"{genome_id}.fa")
    
    def _create_execution_metadata(self, organism_id: str, temp_fasta_path: str) -> Dict:
        return {
            'organism_id': organism_id,
            'temp_fasta_path': temp_fasta_path
        }
    
    def _get_content_type(self, file_type: str) -> str:
        return CONTENT_TYPE_MAPPING.get(file_type, DEFAULT_CONTENT_TYPE)
    
    def _get_genome_file_type(self, file_type: str) -> str:
        return GENOME_FILE_TYPE_MAPPING.get(file_type, UNKNOWN_FILE_TYPE)
