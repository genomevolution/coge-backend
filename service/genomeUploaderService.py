from typing import BinaryIO
from fastapi import UploadFile
from service.minioService import MinIOService
from repository.file import FileRepository
from model.exceptions.fileUploadException import FileUploadException
from model.exceptions.invalidFileTypeException import InvalidFileTypeException
from model.exceptions.fileUrlGenerationException import FileUrlGenerationException
from model.fileUploadResult import FileUploadResult

class GenomeUploaderService:
    """Service responsible for handling genome file uploads"""
    
    def __init__(self, minioService: MinIOService, fileRepository: FileRepository):
        self.minioService = minioService
        self.fileRepository = fileRepository
        self.allowed_extensions = ['.fa', '.fasta', '.fna', '.gz', '.gzi', '.fai']
    
    def _validate_file_extension(self, filename: str) -> None:
        if not filename:
            raise InvalidFileTypeException("", ["genome files with valid filename"])
        
        file_extension = '.' + filename.split('.')[-1].lower()
        if file_extension not in self.allowed_extensions:
            raise InvalidFileTypeException(
                file_extension, 
                self.allowed_extensions
            )
    
    def _upload_genome_file(self, biosample_id: str, genome_id: str, file: UploadFile) -> FileUploadResult:
        file_path = self.minioService.generate_file_path(biosample_id, "genome", file.filename)
        
        file_data = file.file.read()
        file_size = len(file_data)
        file.file.seek(0)
        
        # Upload to MinIO
        self.minioService.upload_file(
            file_data=file.file,
            file_name=file_path,
            content_type=file.content_type or "application/octet-stream",
            file_size=file_size
        )
        
        # Create file record in database
        file_metadata = {   
            "original_filename": file.filename,
            "file_size": file_size,
            "content_type": file.content_type or "application/octet-stream",
            "biosample_id": biosample_id
        }
        file_record = self.fileRepository.create_file(file_path, file_metadata)
        
        # Create genome file link
        self.fileRepository.create_genome_file_link(
            file_record.id, 
            genome_id, 
            "FASTA"
        )
        
        file_url = self.minioService.get_file_url(file_path)
        
        return FileUploadResult(
            message="File uploaded successfully",
            file_path=file_path,
            file_url=file_url,
            biosample_id=biosample_id,
            file_type="genome"
        )
    
    def upload_genome_file(self, biosample_id: str, genome_id: str, file: UploadFile) -> FileUploadResult:
        self._validate_file_extension(file.filename)
        
        try:
            return self._upload_genome_file(biosample_id, genome_id, file)
        except (FileUploadException, FileUrlGenerationException) as e:
            raise e
        except Exception as e:
            raise FileUploadException(file.filename, str(e))
