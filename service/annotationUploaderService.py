from typing import BinaryIO
from fastapi import UploadFile
from service.minioService import MinIOService
from repository.file import FileRepository
from repository.annotation import AnnotationRepository
from model.exceptions.fileUploadException import FileUploadException
from model.exceptions.invalidFileTypeException import InvalidFileTypeException
from model.exceptions.fileUrlGenerationException import FileUrlGenerationException
from model.exceptions.entityNotFoundException import EntityNotFoundException
from model.fileUploadResult import FileUploadResult

class AnnotationUploaderService:
    """Service responsible for handling annotation file uploads"""
    
    def __init__(self, minioService: MinIOService, fileRepository: FileRepository, annotationRepository: AnnotationRepository):
        self.minioService = minioService
        self.fileRepository = fileRepository
        self.annotationRepository = annotationRepository
        self.allowed_extensions = ['.gff3', '.gff', '.gz']
    
    def _validate_file_extension(self, filename: str) -> None:
        if not filename:
            raise InvalidFileTypeException("", ["annotation files with valid filename"])
        
        file_extension = '.' + filename.split('.')[-1].lower()
        if file_extension not in self.allowed_extensions:
            raise InvalidFileTypeException(
                file_extension, 
                self.allowed_extensions
            )
    
    def _upload_annotation_file(self, biosample_id: str, genome_id: str, annotation_id: str, file: UploadFile) -> FileUploadResult:
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
        
        file_metadata = {
            "original_filename": file.filename,
            "file_size": file_size,
            "content_type": file.content_type or "text/plain",
            "biosample_id": biosample_id,
            "annotation_id": annotation_id
        }

        file_record = self.fileRepository.create_file(file_path, file_metadata)
        
        self.fileRepository.create_annotation_file_link(
            file_record.id,
            annotation_id,
            "annotation"
        )
        
        file_url = self.minioService.get_file_url(file_path)
        
        return FileUploadResult(
            message="File uploaded successfully",
            file_path=file_path,
            file_url=file_url,
            file_type="annotation",
            biosample_id=biosample_id
        )
    
    def upload_annotation_file(self, biosample_id: str, genome_id: str, annotation_id: str, file: UploadFile) -> FileUploadResult:
        self._validate_file_extension(file.filename)
        try:
            return self._upload_annotation_file(biosample_id, genome_id, annotation_id, file)
        except (FileUploadException, FileUrlGenerationException, EntityNotFoundException) as e:
            raise e
        except Exception as e:
            raise FileUploadException(file.filename, str(e))
