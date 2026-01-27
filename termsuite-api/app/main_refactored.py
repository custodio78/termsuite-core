"""
Main refactorizado usando routers modulares
"""
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
import json
import os

# Importar routers
from app.routers import web, ollama, tmx, corpus, status
from app.dependencies import (
    file_handler, ollama_translator, jobs, JobStatus
)

app = FastAPI(
    title="LinguaTerms API",
    description="API REST para extracción inteligente de términos técnicos",
    version="1.0.0"
)

# Montar archivos estáticos
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Templates
templates = Jinja2Templates(directory="app/templates")

# Configurar templates en router web
web.set_templates(templates)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Registrar routers
app.include_router(web.router)
app.include_router(ollama.router)
app.include_router(tmx.router)
app.include_router(corpus.router)
app.include_router(status.router)

# NOTA: Los endpoints de exportación se mantienen aquí por ahora
# debido a su complejidad. Se pueden mover a un router separado después.

# Importar funciones de background tasks para exportación
from app.routers.background_tasks import process_tmx_export

# Los endpoints de exportación se mantienen en main.py por ahora
# (líneas 921-1825 del archivo original)
# TODO: Mover a app/routers/export.py en el futuro
