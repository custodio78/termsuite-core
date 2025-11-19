import os
import shutil
import zipfile
from pathlib import Path
from fastapi import UploadFile
from typing import Optional


class FileHandler:
    """Manejador de archivos para la aplicación"""
    
    def __init__(self):
        self.data_dir = Path(os.getenv('DATA_DIR', '/app/data'))
        self.uploads_dir = self.data_dir / 'uploads'
        self.corpus_dir = self.data_dir / 'corpus'
        self.outputs_dir = self.data_dir / 'outputs'
        
        # Crear directorios si no existen
        for directory in [self.uploads_dir, self.corpus_dir, self.outputs_dir]:
            directory.mkdir(parents=True, exist_ok=True)
    
    def save_upload(
        self, 
        file_id: str, 
        file: UploadFile, 
        file_type: str
    ) -> Path:
        """
        Guardar archivo subido
        
        Args:
            file_id: ID único del archivo
            file: Archivo subido
            file_type: Tipo (tmx, corpus)
            
        Returns:
            Path del archivo guardado
        """
        if file_type == 'tmx':
            target_dir = self.uploads_dir / 'tmx'
        elif file_type == 'corpus':
            target_dir = self.uploads_dir / 'corpus'
        else:
            raise ValueError(f"Tipo de archivo no válido: {file_type}")
        
        target_dir.mkdir(parents=True, exist_ok=True)
        
        # Determinar extensión
        ext = Path(file.filename).suffix
        file_path = target_dir / f"{file_id}{ext}"
        
        # Guardar archivo
        with open(file_path, 'wb') as f:
            shutil.copyfileobj(file.file, f)
        
        return file_path
    
    def extract_zip(self, zip_path: Path, corpus_id: str):
        """Extraer archivo ZIP a directorio de corpus"""
        extract_dir = self.corpus_dir / corpus_id
        extract_dir.mkdir(parents=True, exist_ok=True)
        
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            # Extraer solo archivos .txt
            for file_info in zip_ref.filelist:
                if file_info.filename.endswith('.txt'):
                    zip_ref.extract(file_info, extract_dir)
    
    def get_corpus_path(self, corpus_id: str) -> Path:
        """Obtener ruta del corpus"""
        # Primero buscar directorio extraído
        corpus_dir = self.corpus_dir / corpus_id
        if corpus_dir.exists():
            return corpus_dir
        
        # Buscar archivo .txt directo
        txt_file = self.uploads_dir / 'corpus' / f"{corpus_id}.txt"
        if txt_file.exists():
            # Crear directorio y copiar archivo
            corpus_dir.mkdir(parents=True, exist_ok=True)
            shutil.copy(txt_file, corpus_dir / txt_file.name)
            return corpus_dir
        
        raise FileNotFoundError(f"Corpus no encontrado: {corpus_id}")
    
    def get_path(self, path_type: str, filename: str) -> Path:
        """Obtener ruta según tipo"""
        if path_type == 'tmx':
            return self.uploads_dir / 'tmx' / filename
        elif path_type == 'corpus':
            return self.corpus_dir / filename
        elif path_type == 'outputs':
            return self.outputs_dir / filename
        else:
            raise ValueError(f"Tipo de ruta no válido: {path_type}")
    
    def cleanup_old_files(self, days: int = 7):
        """Limpiar archivos antiguos (opcional, para mantenimiento)"""
        import time
        current_time = time.time()
        
        for directory in [self.uploads_dir, self.corpus_dir, self.outputs_dir]:
            for file_path in directory.rglob('*'):
                if file_path.is_file():
                    file_age = current_time - file_path.stat().st_mtime
                    if file_age > (days * 86400):  # días a segundos
                        file_path.unlink()
