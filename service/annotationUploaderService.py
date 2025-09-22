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
    
    def _upload_annotation_file(self, genomeId: str, annotationId: str, file: UploadFile) -> FileUploadResult:
        # Just call to check it exists. No need to assign, if not found, an exception is thrown
        self.annotationRepository.getAnnotation(annotationId)
        
        file_path = f"genomes/{genomeId}/annotations/{annotationId}/{file.filename}"
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
            "genome_id": genomeId,
            "annotation_id": annotationId
        }

        file_record = self.fileRepository.create_file(file_path, file_metadata)
        
        self.fileRepository.create_annotation_file_link(
            file_record.id,
            annotationId,
            "annotation"
        )
        
        file_url = self.minioService.get_file_url(file_path)
        
        return FileUploadResult(
            message="File uploaded successfully",
            file_path=file_path,
            file_url=file_url,
            file_type="annotation"
        )
    
    def upload_annotation_file(self, genomeId: str, annotationId, file: UploadFile) -> FileUploadResult:
        self._validate_file_extension(file.filename)
        try:
            return self._upload_annotation_file(genomeId, annotationId, file)
        except (FileUploadException, FileUrlGenerationException, EntityNotFoundException) as e:
            raise e
        except Exception as e:
            raise FileUploadException(file.filename, str(e))
