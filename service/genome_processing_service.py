import os
from pathlib import Path
from typing import Dict
from service.nextflow_executor_service import NextflowExecutorService
from service.minio_service import MinIOService
from repository.processing_execution import ProcessingExecutionRepository
from repository.file import FileRepository

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
        self.temp_dir = Path(os.getenv('PROCESSING_TEMP_DIR', '/tmp/genome_processing'))
        self.temp_dir.mkdir(parents=True, exist_ok=True)
    
    def start_genome_indexing(
        self,
        organism_id: str,
        genome_id: str,
        fasta_minio_path: str,
        profile: str = "standard"
    ) -> str:
        temp_fasta = self.temp_dir / f"{genome_id}.fa"
        
        try:
            fasta_data = self.minio_service.download_file(fasta_minio_path)
            with open(temp_fasta, 'wb') as f:
                for chunk in fasta_data.stream(amt=8 * 1024 * 1024):
                    f.write(chunk)
            
            execution_id = self.nextflow_executor.execute_genome_indexing(
                organism_id=organism_id,
                genome_id=genome_id,
                fasta_local_path=str(temp_fasta),
                profile=profile
            )
            
            status = self.nextflow_executor.get_execution_status(execution_id)
            
            self.processing_execution_repo.create_execution(
                execution_id=execution_id,
                genome_id=genome_id,
                execution_type='GENOME_INDEXING',
                pid=status.get('pid'),
                profile=profile,
                fasta_path=fasta_minio_path,
                output_dir=status.get('output_dir'),
                log_file=status.get('log_file'),
                metadata={
                    'organism_id': organism_id,
                    'temp_fasta_path': str(temp_fasta)
                }
            )
            
            return execution_id
            
        except Exception as e:
            if temp_fasta.exists():
                temp_fasta.unlink()
            raise e
    
    def get_execution_status(self, execution_id: str) -> Dict:
        status = self.nextflow_executor.get_execution_status(execution_id)
        
        db_execution = self.processing_execution_repo.get_execution_by_id(execution_id)
        if db_execution:
            self.processing_execution_repo.update_execution_status(
                execution_id=execution_id,
                status=status.get('status', 'UNKNOWN'),
                progress=status.get('progress', 0),
                error_message=status.get('error_message')
            )
        
        return status
    
    def finalize_execution(self, execution_id: str) -> Dict:
        status = self.nextflow_executor.get_execution_status(execution_id)
        
        if status.get('status') != 'COMPLETED':
            raise ValueError(f"Execution {execution_id} is not completed. Status: {status.get('status')}")
        
        db_execution = self.processing_execution_repo.get_execution_by_id(execution_id)
        if not db_execution:
            raise ValueError(f"Execution {execution_id} not found in database")
        
        generated_files = status.get('generated_files', {})
        organism_id = db_execution.execution_metadata.get('organism_id')
        genome_id = db_execution.genome_id
        
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
        
        temp_fasta = Path(db_execution.execution_metadata.get('temp_fasta_path', ''))
        if temp_fasta.exists():
            temp_fasta.unlink()
        
        self.processing_execution_repo.update_execution_metadata(
            execution_id,
            {"uploaded_files": uploaded_files}
        )
        
        return {
            "execution_id": execution_id,
            "status": "FINALIZED",
            "uploaded_files": uploaded_files
        }
    
    def _get_content_type(self, file_type: str) -> str:
        """Get content type for file type"""
        content_types = {
            "fasta_gz": "application/gzip",
            "gzi_index": "application/octet-stream",
            "fai_index": "text/plain"
        }
        return content_types.get(file_type, "application/octet-stream")
    
    def _get_genome_file_type(self, file_type: str) -> str:
        """Get genome file type for database"""
        type_mapping = {
            "fasta_gz": "FASTA_GZ",
            "gzi_index": "GZI",
            "fai_index": "FAI"
        }
        return type_mapping.get(file_type, "UNKNOWN")
    
    def cancel_execution(self, execution_id: str) -> bool:
        """Cancel a running execution"""
        cancelled = self.nextflow_executor.cancel_execution(execution_id)
        
        if cancelled:
            self.processing_execution_repo.update_execution_status(
                execution_id,
                status='CANCELLED'
            )
        
        return cancelled

