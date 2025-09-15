class FileDeleteException(Exception):
    """Exception raised when file deletion fails"""
    
    def __init__(self, file_name: str, original_error: str):
        self.file_name = file_name
        self.original_error = original_error
        super().__init__(f"Failed to delete file '{file_name}': {original_error}")
