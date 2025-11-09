class InvalidFileTypeException(Exception):
    """Exception raised when file type is invalid"""
    
    def __init__(self, file_type: str, allowed_types: list):
        self.file_type = file_type
        self.allowed_types = allowed_types
        super().__init__(f"Invalid file type '{file_type}'. Must be one of: {', '.join(allowed_types)}")
