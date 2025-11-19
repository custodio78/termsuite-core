#!/usr/bin/env python3
"""
Cliente de ejemplo para TermSuite API
Muestra cómo usar la API desde Python
"""
import requests
import time
from pathlib import Path


class TermSuiteClient:
    """Cliente Python para TermSuite API"""
    
    def __init__(self, base_url: str = "http://localhost:7000"):
        self.base_url = base_url
    
    def upload_tmx(self, tmx_path: str) -> str:
        """Subir memoria TMX"""
        with open(tmx_path, 'rb') as f:
            response = requests.post(
                f"{self.base_url}/api/upload-tmx",
                files={'file': f}
            )
        response.raise_for_status()
        return response.json()['file_id']
    
    def upload_corpus(self, corpus_path: str) -> str:
        """Subir corpus (txt o zip)"""
        with open(corpus_path, 'rb') as f:
            response = requests.post(
                f"{self.base_url}/api/upload-corpus",
                files={'file': f}
            )
        response.raise_for_status()
        return response.json()['file_id']
    
    def extract_terms(
        self,
        corpus_id: str,
        language: str = 'en',
        min_frequency: int = 2,
        tmx_id: str = None
    ) -> str:
        """Iniciar extracción de términos"""
        payload = {
            'corpus_id': corpus_id,
            'language': language,
            'min_frequency': min_frequency,
            'use_tmx': tmx_id is not None,
            'tmx_id': tmx_id
        }
        response = requests.post(
            f"{self.base_url}/api/extract",
            json=payload
        )
        response.raise_for_status()
        return response.json()['job_id']
    
    def get_status(self, job_id: str) -> dict:
        """Obtener estado del trabajo"""
        response = requests.get(f"{self.base_url}/api/status/{job_id}")
        response.raise_for_status()
        return response.json()
    
    def wait_for_completion(self, job_id: str, timeout: int = 600) -> bool:
        """Esperar a que termine el trabajo"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            status = self.get_status(job_id)
            
            print(f"Estado: {status['status']} ({status['progress']}%)")
            
            if status['status'] == 'completed':
                return True
            elif status['status'] == 'failed':
                raise Exception(f"Trabajo falló: {status.get('error')}")
            
            time.sleep(3)
        
        raise TimeoutError("Tiempo de espera excedido")
    
    def download_excel(self, job_id: str, output_path: str):
        """Descargar archivo Excel"""
        response = requests.get(
            f"{self.base_url}/api/export/excel/{job_id}"
        )
        response.raise_for_status()
        
        with open(output_path, 'wb') as f:
            f.write(response.content)


def main():
    """Ejemplo de uso"""
    # Crear cliente
    client = TermSuiteClient()
    
    print("=== TermSuite API - Cliente de Ejemplo ===\n")
    
    # 1. Subir TMX (opcional)
    tmx_id = None
    if Path("ejemplo.tmx").exists():
        print("📤 Subiendo TMX...")
        tmx_id = client.upload_tmx("ejemplo.tmx")
        print(f"✅ TMX subido: {tmx_id}\n")
    
    # 2. Subir corpus
    print("📤 Subiendo corpus...")
    corpus_id = client.upload_corpus("ejemplo.txt")
    print(f"✅ Corpus subido: {corpus_id}\n")
    
    # 3. Extraer términos
    print("⚙️  Iniciando extracción...")
    job_id = client.extract_terms(
        corpus_id=corpus_id,
        language='en',
        min_frequency=2,
        tmx_id=tmx_id
    )
    print(f"✅ Trabajo iniciado: {job_id}\n")
    
    # 4. Esperar completación
    print("⏳ Esperando completación...")
    client.wait_for_completion(job_id)
    print("✅ Extracción completada\n")
    
    # 5. Descargar Excel
    print("⬇️  Descargando resultados...")
    client.download_excel(job_id, "resultados.xlsx")
    print("✅ Archivo descargado: resultados.xlsx\n")
    
    print("🎉 ¡Proceso completado exitosamente!")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        exit(1)
