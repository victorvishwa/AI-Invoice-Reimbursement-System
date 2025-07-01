import os
from typing import Optional, List
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # MongoDB Configuration
    mongodb_uri: str = "mongodb://localhost:27017"
    database_name: str = "invoice_reimbursement"
    
    # LLM Configuration
    llm_provider: str = "groq"  # groq, openai, or google
    groq_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None
    google_api_key: Optional[str] = None
    
    # Embedding Configuration
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    
    # Application Configuration
    max_file_size: int = 50 * 1024 * 1024  # 50MB
    allowed_pdf_extensions: str = ".pdf"
    allowed_zip_extensions: str = ".zip"
    
    # Vector Search Configuration
    vector_dimension: int = 384  # for all-MiniLM-L6-v2
    similarity_threshold: float = 0.7
    
    @property
    def allowed_pdf_extensions_list(self) -> List[str]:
        """Convert comma-separated string to list"""
        return [ext.strip() for ext in self.allowed_pdf_extensions.split(",")]
    
    @property
    def allowed_zip_extensions_list(self) -> List[str]:
        """Convert comma-separated string to list"""
        return [ext.strip() for ext in self.allowed_zip_extensions.split(",")]
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings() 