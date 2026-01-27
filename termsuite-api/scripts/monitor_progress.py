#!/usr/bin/env python3
"""
Monitor continuo del progreso de traducción
"""

import requests
import time
import sys

def monitor_progress():
    """Monitor continuo del progreso"""
    
    base_url = "http://localhost:7000"
    job_id = "3c9bbe12-c199-44dc-a013-c392deeebe59"
    
    print(f"🔄 Monitoreando progreso en tiempo real...")
    print(f"Job ID: {job_id}")
    print(f"Presiona Ctrl+C para salir\n")
    
    last_progress = -1
    
    try:
        while True:
            try:
                response = requests.get(f"{base_url}/api/status/{job_id}")
                if response.status_code == 200:
                    status_data = response.json()
                    
                    current_progress = status_data['progress']
                    
                    # Solo mostrar si hay cambio en el progreso
                    if current_progress != last_progress:
                        timestamp = time.strftime("%H:%M:%S")
                        print(f"[{timestamp}] {current_progress:3d}% - {status_data['message']}")
                        last_progress = current_progress
                    
                    if status_data['status'] == 'completed':
                        print(f"\n🎉 ¡Proceso completado exitosamente!")
                        break
                    elif status_data['status'] == 'failed':
                        print(f"\n❌ Proceso falló: {status_data.get('error', 'Error desconocido')}")
                        break
                else:
                    print(f"❌ Error API: {response.status_code}")
                    break
                    
            except requests.exceptions.RequestException as e:
                print(f"❌ Error de conexión: {e}")
                break
            
            time.sleep(5)  # Verificar cada 5 segundos
            
    except KeyboardInterrupt:
        print(f"\n⏹️ Monitoreo detenido por el usuario")

if __name__ == "__main__":
    monitor_progress()