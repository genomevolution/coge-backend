from typing import BinaryIO
from fastapi import UploadFile
from service.minioService import MinIOService
from model.exceptions.fileUploadException import FileUploadException
from model.exceptions.invalidFileTypeException import InvalidFileTypeException
from model.exceptions.fileUrlGenerationException import FileUrlGenerationException
from model.fileUploadResult import FileUploadResult

class AnnotationUploaderService:
    """Service responsible for handling annotation file uploads"""
    
    def __init__(self, minioService: MinIOService):
        self.minioService = minioService
        self.allowed_extensions = ['.gff3', '.gff']
    
    def _validate_file_extension(self, filename: str) -> None:
        if not filename:
            raise InvalidFileTypeException("", ["annotation files with valid filename"])
        
        file_extension = '.' + filename.split('.')[-1].lower()
        if file_extension not in self.allowed_extensions:
            raise InvalidFileTypeException(
                file_extension, 
                self.allowed_extensions
            )
    
    def _upload_annotation_file(self, biosample_id: str, file: UploadFile) -> FileUploadResult:
        file_path = self.minioService.generate_file_path(biosample_id, "annotation", file.filename)
        
        file_data = file.file.read()
        file_size = len(file_data)
        file.file.seek(0)
        
        self.minioService.upload_file(
            file_data=file.file,
            file_name=file_path,
            content_type=file.content_type or "text/plain",
            file_size=file_size
        )
        
        file_url = self.minioService.get_file_url(file_path)
        
        return FileUploadResult(
            message="File uploaded successfully",
            file_path=file_path,
            file_url=file_url,
            biosample_id=biosample_id,
            file_type="annotation"
        )
    
    def upload_annotation_file(self, biosample_id: str, file: UploadFile) -> FileUploadResult:
        self._validate_file_extension(file.filename)
        
        try:
            return self._upload_annotation_file(biosample_id, file)
        except (FileUploadException, FileUrlGenerationException) as e:
            raise e
        except Exception as e:
            raise FileUploadException(file.filename, str(e))
