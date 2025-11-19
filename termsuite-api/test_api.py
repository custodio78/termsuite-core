#!/usr/bin/env python3
"""
Script de prueba para TermSuite API
"""
import requests
import time
import sys
from pathlib import Path


BASE_URL = "http://localhost:7000"


def test_health():
    """Probar que la API está funcionando"""
    print("🔍 Probando salud de la API...")
    response = requests.get(f"{BASE_URL}/")
    print(f"✅ API respondiendo: {response.json()['message']}")
    return True


def test_upload_tmx(tmx_file: str, language: str = 'en'):
    """Probar subida de TMX"""
    print(f"\n📤 Subiendo TMX: {tmx_file} (idioma: {language})")
    
    if not Path(tmx_file).exists():
        print(f"❌ Archivo no encontrado: {tmx_file}")
        return None
    
    with open(tmx_file, 'rb') as f:
        response = requests.post(
            f"{BASE_URL}/api/upload-tmx",
            files={'file': f},
            params={'language': language}
        )
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ TMX subido: {data['file_id']}")
        print(f"   {data['message']}")
        return data['file_id']
    else:
        print(f"❌ Error: {response.text}")
        return None


def test_upload_corpus(corpus_file: str):
    """Probar subida de corpus"""
    print(f"\n📤 Subiendo corpus: {corpus_file}")
    
    if not Path(corpus_file).exists():
        print(f"❌ Archivo no encontrado: {corpus_file}")
        return None
    
    with open(corpus_file, 'rb') as f:
        response = requests.post(
            f"{BASE_URL}/api/upload-corpus",
            files={'file': f}
        )
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Corpus subido: {data['file_id']}")
        return data['file_id']
    else:
        print(f"❌ Error: {response.text}")
        return None


def test_extract(corpus_id: str, tmx_id: str = None):
    """Probar extracción de términos"""
    print(f"\n⚙️  Iniciando extracción...")
    
    payload = {
        "corpus_id": corpus_id,
        "language": "en",
        "min_frequency": 2,
        "use_tmx": tmx_id is not None,
        "tmx_id": tmx_id
    }
    
    response = requests.post(
        f"{BASE_URL}/api/extract",
        json=payload
    )
    
    if response.status_code == 200:
        data = response.json()
        job_id = data['job_id']
        print(f"✅ Trabajo iniciado: {job_id}")
        return job_id
    else:
        print(f"❌ Error: {response.text}")
        return None


def test_status(job_id: str, wait: bool = True):
    """Probar consulta de estado"""
    print(f"\n🔄 Consultando estado del trabajo...")
    
    while True:
        response = requests.get(f"{BASE_URL}/api/status/{job_id}")
        
        if response.status_code == 200:
            data = response.json()
            status = data['status']
            progress = data['progress']
            message = data['message']
            
            print(f"   Estado: {status} ({progress}%) - {message}")
            
            if status == 'completed':
                print(f"✅ Trabajo completado")
                return True
            elif status == 'failed':
                print(f"❌ Trabajo falló: {data.get('error')}")
                return False
            elif not wait:
                return None
            
            time.sleep(3)
        else:
            print(f"❌ Error: {response.text}")
            return False


def test_download(job_id: str, output_file: str = "resultados.xlsx"):
    """Probar descarga de Excel"""
    print(f"\n⬇️  Descargando resultados...")
    
    response = requests.get(f"{BASE_URL}/api/export/excel/{job_id}")
    
    if response.status_code == 200:
        with open(output_file, 'wb') as f:
            f.write(response.content)
        print(f"✅ Archivo descargado: {output_file}")
        return True
    else:
        print(f"❌ Error: {response.text}")
        return False


def main():
    """Ejecutar pruebas completas"""
    print("=" * 60)
    print("🧪 PRUEBAS DE TERMSUITE API")
    print("=" * 60)
    
    # Verificar argumentos
    if len(sys.argv) < 2:
        print("\nUso:")
        print("  python test_api.py <corpus.txt> [memoria.tmx]")
        print("\nEjemplo:")
        print("  python test_api.py corpus.txt")
        print("  python test_api.py corpus.txt memoria.tmx")
        sys.exit(1)
    
    corpus_file = sys.argv[1]
    tmx_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    try:
        # 1. Salud
        test_health()
        
        # 2. Subir TMX (opcional)
        tmx_id = None
        if tmx_file:
            tmx_id = test_upload_tmx(tmx_file)
        
        # 3. Subir corpus
        corpus_id = test_upload_corpus(corpus_file)
        if not corpus_id:
            sys.exit(1)
        
        # 4. Extraer
        job_id = test_extract(corpus_id, tmx_id)
        if not job_id:
            sys.exit(1)
        
        # 5. Esperar
        if not test_status(job_id, wait=True):
            sys.exit(1)
        
        # 6. Descargar
        if not test_download(job_id):
            sys.exit(1)
        
        print("\n" + "=" * 60)
        print("✅ TODAS LAS PRUEBAS PASARON")
        print("=" * 60)
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Pruebas interrumpidas por el usuario")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error inesperado: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
