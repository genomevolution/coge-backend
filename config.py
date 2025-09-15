import os
from typing import Optional

class Config:
    """Centralized configuration management for all environment variables"""
    
    DB_USER: str
    DB_PASSWORD: str
    DB_HOST: str
    DB_PORT: int
    DB_NAME: str
    
    MINIO_ENDPOINT: str
    MINIO_ACCESS_KEY: str
    MINIO_SECRET_KEY: str
    MINIO_BUCKET_NAME: str
    
    def __init__(self):
        """Initialize configuration from environment variables"""
        self._load_database_config()
        self._load_minio_config()
    
    def _load_database_config(self):
        """Load database configuration from environment variables"""
        self.DB_USER = self._get_required_env("DB_USER")
        self.DB_PASSWORD = self._get_required_env("DB_PASSWORD")
        self.DB_HOST = self._get_required_env("DB_HOST")
        self.DB_PORT = self._get_required_env_int("DB_PORT")
        self.DB_NAME = self._get_required_env("DB_NAME")
    
    def _load_minio_config(self):
        self.MINIO_ENDPOINT = self._get_env_with_default("MINIO_ENDPOINT", "localhost:9000")
        self.MINIO_ACCESS_KEY = self._get_env_with_default("MINIO_ACCESS_KEY", "minioadmin")
        self.MINIO_SECRET_KEY = self._get_env_with_default("MINIO_SECRET_KEY", "minioadmin123")
        self.MINIO_BUCKET_NAME = self._get_env_with_default("MINIO_BUCKET_NAME", "genomes")
    
    def _get_required_env(self, key: str) -> str:
        value = os.environ.get(key)
        if value is None:
            raise Exception(f"Required environment variable {key} is not set")
        return value
    
    def _get_required_env_int(self, key: str) -> int:
        value = self._get_required_env(key)
        try:
            return int(value)
        except ValueError:
            raise Exception(f"Environment variable {key} must be a valid integer, got: {value}")
    
    def _get_env_with_default(self, key: str, default: str) -> str:
        return os.environ.get(key, default)
    
    def get_database_url(self) -> str:
        return f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
    
    def get_minio_config(self) -> dict:
        return {
            "endpoint": self.MINIO_ENDPOINT,
            "access_key": self.MINIO_ACCESS_KEY,
            "secret_key": self.MINIO_SECRET_KEY,
            "bucket_name": self.MINIO_BUCKET_NAME
        }

config = Config()
