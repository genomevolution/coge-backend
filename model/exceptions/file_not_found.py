class FileNotFoundException(Exception):
    """Exception raised when a file is not found"""
    
    def __init__(self, file_name: str):
        self.file_name = file_name
        super().__init__(f"File '{file_name}' not found")
