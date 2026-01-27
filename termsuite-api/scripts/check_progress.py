#!/usr/bin/env python3
"""
Verificar progreso de traducción en tiempo real
"""

import requests
import time

def check_progress():
    """Verificar progreso del job actual"""
    
    base_url = "http://localhost:7000"
    job_id = "6fc5a189-38bc-4db2-804d-5a8ac45dcad0"  # Nuevo job ID del log
    
    print(f"=== Monitoreando Job: {job_id} ===")
    
    try:
        response = requests.get(f"{base_url}/api/status/{job_id}")
        if response.status_code == 200:
            status_data = response.json()
            
            print(f"\n📊 Estado actual:")
            print(f"   Estado: {status_data['status']}")
            print(f"   Progreso: {status_data['progress']}%")
            print(f"   Mensaje: {status_data['message']}")
            
            if 'error' in status_data:
                print(f"   ❌ Error: {status_data['error']}")
            
            return status_data
        else:
            print(f"❌ Error: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

if __name__ == "__main__":
    status = check_progress()
    
    if status and status['status'] == 'completed':
        print(f"\n🎉 ¡Proceso completado!")
        print(f"Puedes descargar el resultado desde la interfaz web")
    elif status and status['status'] == 'failed':
        print(f"\n❌ Proceso falló")
    elif status and status['status'] == 'processing':
        print(f"\n⏳ Proceso en curso... {status['progress']}%")
        print(f"Mensaje: {status['message']}")
    else:
        print(f"\n❓ Estado desconocido")