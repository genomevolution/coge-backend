from typing import BinaryIO
from minio import Minio
from minio.commonconfig import CopySource
from minio.error import S3Error
from config import config
from model.exceptions.bucket_cannot_be_created import BucketCannotBeCreatedException
from model.exceptions.file_upload import FileUploadException
from model.exceptions.file_not_found import FileNotFoundException
from model.exceptions.file_download import FileDownloadException
from model.exceptions.file_url_generation import FileUrlGenerationException


GENOME_FILE_PATH_TEMPLATE = "{organism_id}/genomes/{original_filename}"
ANNOTATION_FILE_PATH_TEMPLATE = "annotation/{annotation_id}/{original_filename}"
IMPORT_STAGING_PATH_TEMPLATE = "staging/imports/{import_id}/{category}/{original_filename}"

class MinIOService:
    def __init__(self):
        minio_config = config.get_minio_config()
        self.minio_client = Minio(
            endpoint=minio_config["endpoint"],
            access_key=minio_config["access_key"],
            secret_key=minio_config["secret_key"],
            secure=False
        )
        self.bucket_name = minio_config["bucket_name"]
        self._ensure_bucket_exists()

    def _ensure_bucket_exists(self):
        try:
            if not self.minio_client.bucket_exists(self.bucket_name):
                self.minio_client.make_bucket(self.bucket_name)
        except S3Error as e:
            raise BucketCannotBeCreatedException(self.bucket_name, str(e))

    def upload_file(self, file_data: BinaryIO, file_name: str, content_type: str, file_size: int) -> str:
        try:
            self.minio_client.put_object(
                bucket_name=self.bucket_name,
                object_name=file_name,
                data=file_data,
                length=file_size,
                content_type=content_type
            )
            return file_name
        except S3Error as e:
            raise FileUploadException(file_name, str(e))

    def download_file(self, file_name: str) -> BinaryIO:
        try:
            response = self.minio_client.get_object(self.bucket_name, file_name)
            return response
        except S3Error as e:
            if e.code == "NoSuchKey":
                raise FileNotFoundException(file_name)
            raise FileDownloadException(file_name, str(e))

    def generate_genome_file_path(self, organism_id: str, original_filename: str) -> str:
        return GENOME_FILE_PATH_TEMPLATE.format(
            organism_id=organism_id,
            original_filename=original_filename
        )

    def generate_annotation_file_path(self, annotation_id: str, original_filename: str) -> str:
        return ANNOTATION_FILE_PATH_TEMPLATE.format(
            annotation_id=annotation_id,
            original_filename=original_filename
        )

    def generate_import_staging_path(
        self,
        import_id: str,
        category: str,
        original_filename: str
    ) -> str:
        return IMPORT_STAGING_PATH_TEMPLATE.format(
            import_id=import_id,
            category=category,
            original_filename=original_filename
        )

    def copy_file(self, source_path: str, destination_path: str) -> str:
        try:
            self.minio_client.copy_object(
                self.bucket_name,
                destination_path,
                CopySource(self.bucket_name, source_path)
            )
            return destination_path
        except S3Error as error:
            raise FileUploadException(destination_path, str(error)) from error

    def delete_file(self, file_path: str) -> None:
        try:
            self.minio_client.remove_object(self.bucket_name, file_path)
        except S3Error as error:
            raise FileUploadException(file_path, str(error)) from error

    def delete_prefix(self, prefix: str) -> None:
        try:
            for stored_object in self.minio_client.list_objects(
                self.bucket_name,
                prefix=prefix,
                recursive=True
            ):
                self.minio_client.remove_object(
                    self.bucket_name,
                    stored_object.object_name
                )
        except S3Error as error:
            raise FileUploadException(prefix, str(error)) from error

    def get_file_url(self, file_name: str, expires_in_seconds: int = 3600) -> str:
        try:
            from datetime import timedelta
            url = self.minio_client.presigned_get_object(
                bucket_name=self.bucket_name,
                object_name=file_name,
                expires=timedelta(seconds=expires_in_seconds)
            )
            return url
        except S3Error as e:
            raise FileUrlGenerationException(file_name, str(e))
