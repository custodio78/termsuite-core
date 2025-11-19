from pydantic import BaseModel, Field
from typing import Optional, List
from enum import Enum


class JobStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class Language(str, Enum):
    EN = "en"
    ES = "es"
    FR = "fr"
    DE = "de"
    IT = "it"
    PT = "pt"


class ExtractionRequest(BaseModel):
    corpus_id: str = Field(..., description="ID del corpus subido")
    language: Language = Field(..., description="Idioma del corpus")
    min_frequency: int = Field(default=2, ge=1, description="Frecuencia mínima de términos")
    max_terms: Optional[int] = Field(default=None, description="Número máximo de términos")
    use_tmx: bool = Field(default=False, description="Usar memoria TMX para filtrado")
    tmx_id: Optional[str] = Field(default=None, description="ID de la memoria TMX")


class ExtractionResponse(BaseModel):
    job_id: str
    status: JobStatus
    message: str


class JobStatusResponse(BaseModel):
    job_id: str
    status: JobStatus
    progress: int = Field(ge=0, le=100)
    message: str
    result_file: Optional[str] = None
    error: Optional[str] = None


class UploadResponse(BaseModel):
    file_id: str
    filename: str
    size: int
    message: str


class TermEntry(BaseModel):
    term: str
    frequency: int
    doc_frequency: int
    specificity: float
    pattern: str
    in_tmx: bool = False
