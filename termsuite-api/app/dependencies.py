"""
Dependencias compartidas para los routers
Centraliza la inicialización de servicios y estado
"""
from typing import Dict, List
from app.services.termsuite import TermSuiteService
from app.services.tmx_parser import TMXParser
from app.services.excel_export import ExcelExporter
from app.services.ollama_translator import OllamaTranslator
from app.utils.file_handler import FileHandler

# Servicios globales (singletons)
termsuite_service = TermSuiteService()
tmx_parser = TMXParser()
excel_exporter = ExcelExporter()
ollama_translator = OllamaTranslator()
file_handler = FileHandler()

# Estado de trabajos en memoria (en producción usar Redis/DB)
jobs: Dict[str, dict] = {}

# Logs de Ollama en tiempo real
ollama_logs: List[dict] = []


def add_ollama_log(action: str, term: str = None, status: str = None, details: str = None, prompt: str = None, response: str = None):
    """Agregar log de Ollama con prompt y respuesta"""
    import datetime
    log_entry = {
        "timestamp": datetime.datetime.now().isoformat(),
        "action": action,
        "term": term,
        "status": status,
        "details": details,
        "prompt": prompt,
        "response": response
    }
    ollama_logs.append(log_entry)
    
    # Mantener solo los últimos 200 logs
    if len(ollama_logs) > 200:
        ollama_logs.pop(0)
    
    print(f"OLLAMA LOG: {action} - {term} - {status} - {details}")


# Configurar logging para Ollama
ollama_translator.log_callback = add_ollama_log
