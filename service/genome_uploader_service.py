from fastapi import UploadFile
from service.minio_service import MinIOService
from repository.file import FileRepository
from model.exceptions.file_upload import FileUploadException
from model.exceptions.invalid_file_type import InvalidFileTypeException
from model.exceptions.file_url_generation import FileUrlGenerationException
from model.dto.file_upload_result import FileUploadResult


GENOME_ALLOWED_EXTENSIONS = ('.fa', '.fa.gz')
GENOME_CONTENT_TYPE = "application/octet-stream"
GENOME_FILE_TYPE = "FASTA"
GENOME_UPLOAD_RESULT_TYPE = "genome"
FILE_UPLOAD_SUCCESS_MESSAGE = "File uploaded successfully"
INVALID_GENOME_FILENAME_TYPE = "genome files with valid filename"


class GenomeUploaderService:
    def __init__(self, minioService: MinIOService, fileRepository: FileRepository):
        self.minioService = minioService
        self.fileRepository = fileRepository
    
    def _validate_file_extension(self, filename: str) -> None:
        if not filename:
            raise InvalidFileTypeException("", [INVALID_GENOME_FILENAME_TYPE])
        
        normalized_filename = filename.lower()
        if not any(normalized_filename.endswith(extension) for extension in GENOME_ALLOWED_EXTENSIONS):
            raise InvalidFileTypeException(
                filename,
                list(GENOME_ALLOWED_EXTENSIONS)
            )
    
    def _upload_genome_file(self, organism_id: str, genome_id: str, file: UploadFile) -> FileUploadResult:
        file_path = self.minioService.generate_genome_file_path(
            organism_id,
            file.filename
        )
        
        file_data = file.file.read()
        file_size = len(file_data)
        file.file.seek(0)
        
        content_type = file.content_type or GENOME_CONTENT_TYPE
        self.minioService.upload_file(
            file_data=file.file,
            file_name=file_path,
            content_type=content_type,
            file_size=file_size
        )
        
        file_metadata = {   
            "original_filename": file.filename,
            "file_size": file_size,
            "content_type": content_type,
            "organism_id": organism_id
        }
        file_record = self.fileRepository.create_file(file_path, file_metadata)
        
        self.fileRepository.create_genome_file_link(
            file_record.id, 
            genome_id, 
            GENOME_FILE_TYPE
        )
        
        file_url = self.minioService.get_file_url(file_path)
        
        return FileUploadResult(
            message=FILE_UPLOAD_SUCCESS_MESSAGE,
            file_path=file_path,
            file_url=file_url,
            file_type=GENOME_UPLOAD_RESULT_TYPE
        )
    
    def upload_genome_file(self, organism_id: str, genome_id: str, file: UploadFile) -> FileUploadResult:
        self._validate_file_extension(file.filename)
        
        try:
            return self._upload_genome_file(organism_id, genome_id, file)
        except (FileUploadException, FileUrlGenerationException):
            raise
        except Exception as error:
            raise FileUploadException(file.filename, str(error)) from error
