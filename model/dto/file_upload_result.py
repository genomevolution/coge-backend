from dataclasses import dataclass

@dataclass
class FileUploadResult:
    message: str
    file_path: str
    file_url: str
    file_type: str
    
    def to_dict(self) -> dict:
        return {
            "message": self.message,
            "file_path": self.file_path,
            "file_url": self.file_url,
            "file_type": self.file_type
        }
