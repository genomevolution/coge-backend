from dataclasses import dataclass

@dataclass
class FileUploadResult:
    """Result of a file upload operation"""
    
    message: str
    file_path: str
    file_url: str
    file_type: str
    organism_id: str
    
    def __init__(self, message: str, file_path: str, file_url: str, file_type: str, organism_id: str):
        self.message = message
        self.file_path = file_path
        self.file_url = file_url
        self.file_type = file_type
        self.organism_id = organism_id
    
    def to_dict(self) -> dict:
        return {
            "message": self.message,
            "file_path": self.file_path,
            "file_url": self.file_url,
            "file_type": self.file_type,
            "organism_id": self.organism_id
        }
