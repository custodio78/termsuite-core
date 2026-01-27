"""
Router para endpoints de corpus (extracción de términos)
"""
import os
import uuid
from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks

from app.models import UploadResponse, ExtractionRequest, ExtractionResponse, JobStatus
from app.dependencies import file_handler, jobs
from app.routers.background_tasks import process_extraction

router = APIRouter(prefix="/api", tags=["corpus"])


@router.post("/upload-corpus", response_model=UploadResponse)
async def upload_corpus(file: UploadFile = File(...)):
    """Subir corpus de texto (.txt o .zip con múltiples .txt)"""
    allowed_extensions = ['.txt', '.zip']
    if not any(file.filename.endswith(ext) for ext in allowed_extensions):
        raise HTTPException(
            status_code=400, 
            detail="Solo se permiten archivos .txt o .zip"
        )
    
    corpus_id = str(uuid.uuid4())
    file_path = file_handler.save_upload(corpus_id, file, "corpus")
    
    # Si es ZIP, extraer
    if file.filename.endswith('.zip'):
        file_handler.extract_zip(file_path, corpus_id)
    
    return UploadResponse(
        file_id=corpus_id,
        filename=file.filename,
        size=os.path.getsize(file_path),
        message="Corpus subido exitosamente"
    )


@router.post("/extract", response_model=ExtractionResponse)
async def extract_terms(
    request: ExtractionRequest,
    background_tasks: BackgroundTasks
):
    """Extraer términos del corpus"""
    import uuid
    job_id = str(uuid.uuid4())
    
    # Validar que existe el corpus
    corpus_path = file_handler.get_corpus_path(request.corpus_id)
    if not corpus_path.exists():
        raise HTTPException(status_code=404, detail="Corpus no encontrado")
    
    # Validar TMX si se especifica
    if request.use_tmx and request.tmx_id:
        tmx_terms_path = file_handler.get_path("tmx", f"{request.tmx_id}_terms.json")
        if not tmx_terms_path.exists():
            raise HTTPException(status_code=404, detail="TMX no encontrado")
    
    # Crear trabajo
    jobs[job_id] = {
        "status": JobStatus.PENDING,
        "progress": 0,
        "message": "Trabajo en cola",
        "request": request.dict()
    }
    
    # Ejecutar en background
    background_tasks.add_task(
        process_extraction,
        job_id,
        request
    )
    
    return ExtractionResponse(
        job_id=job_id,
        status=JobStatus.PENDING,
        message="Extracción iniciada"
    )
