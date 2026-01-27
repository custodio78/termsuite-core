"""
Router para interfaces web (HTML)
"""
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

router = APIRouter()

# Templates (se inicializan en main.py)
templates = None


def set_templates(templates_instance):
    """Configurar instancia de templates desde main.py"""
    global templates
    templates = templates_instance


@router.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Página principal con interfaz web mejorada"""
    return templates.TemplateResponse("index_v2.html", {"request": request})


@router.get("/classic", response_class=HTMLResponse)
async def classic_interface(request: Request):
    """Interfaz clásica (legacy)"""
    return templates.TemplateResponse("index.html", {"request": request})


@router.get("/monitor", response_class=HTMLResponse)
async def ollama_monitor(request: Request):
    """Monitor de Ollama en tiempo real"""
    return templates.TemplateResponse("ollama_monitor.html", {"request": request})


@router.get("/api")
async def api_info():
    """Información de la API"""
    return {
        "message": "LinguaTerms API",
        "version": "1.0.0",
        "endpoints": {
            "upload_tmx": "/api/upload-tmx",
            "upload_corpus": "/api/upload-corpus",
            "extract": "/api/extract",
            "status": "/api/status/{job_id}",
            "export": "/api/export/excel/{job_id}",
            "export_tmx": "/api/export/tmx-excel/{tmx_id}",
            "ollama_status": "/api/ollama/status"
        }
    }
