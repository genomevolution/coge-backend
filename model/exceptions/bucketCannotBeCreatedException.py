class BucketCannotBeCreatedException(Exception):
    """Exception raised when a MinIO bucket cannot be created"""
    
    def __init__(self, bucket_name: str, original_error: str):
        self.bucket_name = bucket_name
        self.original_error = original_error
        super().__init__(f"Failed to create bucket '{bucket_name}': {original_error}")
