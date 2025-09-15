from typing import BinaryIO
from minio import Minio
from minio.error import S3Error
from config import config
from model.exceptions.bucketCannotBeCreatedException import BucketCannotBeCreatedException
from model.exceptions.fileUploadException import FileUploadException
from model.exceptions.fileNotFoundException import FileNotFoundException
from model.exceptions.fileDownloadException import FileDownloadException
from model.exceptions.fileDeleteException import FileDeleteException
from model.exceptions.invalidFileTypeException import InvalidFileTypeException
from model.exceptions.fileUrlGenerationException import FileUrlGenerationException

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

    def delete_file(self, file_name: str) -> bool:
        try:
            self.minio_client.remove_object(self.bucket_name, file_name)
            return True
        except S3Error as e:
            raise FileDeleteException(file_name, str(e))

    def generate_file_path(self, biosample_id: str, file_type: str, original_filename: str) -> str:
        if file_type == "genome":
            return f"{biosample_id}/genomes/{original_filename}"
        elif file_type == "annotation":
            return f"{biosample_id}/annotation/{original_filename}"
        else:
            raise InvalidFileTypeException(file_type, ["genome", "annotation"])

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
