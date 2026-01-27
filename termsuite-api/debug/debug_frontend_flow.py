#!/usr/bin/env python3
"""
Script para debuggear el flujo de traducciones automáticas
"""

import requests
import json
import time

API_BASE = "http://localhost:7000"

def test_automatic_translation_flow():
    """Probar el flujo completo de traducciones automáticas"""
    
    print("=== DEBUGGING AUTOMATIC TRANSLATION FLOW ===\n")
    
    # 1. Verificar estado de Ollama
    print("1. Verificando estado de Ollama...")
    try:
        response = requests.get(f"{API_BASE}/api/ollama/status")
        ollama_status = response.json()
        print(f"   Ollama disponible: {ollama_status.get('available', False)}")
        if ollama_status.get('available'):
            print(f"   Modelo: {ollama_status.get('model', 'N/A')}")
        else:
            print(f"   Error: {ollama_status.get('error', 'N/A')}")
    except Exception as e:
        print(f"   Error conectando: {e}")
        return
    
    # 2. Buscar un TMX existente para probar
    print("\n2. Buscando TMX existente...")
    import os
    tmx_dir = "data/uploads/tmx"
    tmx_files = []
    
    if os.path.exists(tmx_dir):
        for file in os.listdir(tmx_dir):
            if file.endswith('.tmx'):
                tmx_id = file.split('.')[0]
                tmx_files.append((tmx_id, file))
    
    if not tmx_files:
        print("   No se encontraron archivos TMX. Sube un TMX primero.")
        return
    
    # Usar el primer TMX encontrado
    tmx_id, tmx_filename = tmx_files[0]
    print(f"   Usando TMX: {tmx_filename} (ID: {tmx_id})")
    
    # 3. Obtener idiomas disponibles
    print("\n3. Obteniendo idiomas disponibles...")
    try:
        response = requests.get(f"{API_BASE}/api/tmx-languages/{tmx_id}")
        if response.ok:
            lang_data = response.json()
            available_languages = lang_data.get('available_languages', [])
            print(f"   Idiomas disponibles: {available_languages}")
            
            if len(available_languages) < 2:
                print("   Se necesitan al menos 2 idiomas para probar traducciones automáticas")
                return
                
            # Seleccionar idiomas (preferir español como origen)
            source_lang = 'es' if 'es' in available_languages else available_languages[0]
            target_lang = next((lang for lang in available_languages if lang != source_lang), None)
            
            if not target_lang:
                print("   No se pudo determinar idioma destino")
                return
                
            print(f"   Idioma origen: {source_lang}")
            print(f"   Idioma destino: {target_lang}")
        else:
            print(f"   Error obteniendo idiomas: {response.text}")
            return
    except Exception as e:
        print(f"   Error: {e}")
        return
    
    # 4. Probar extracción con traducciones automáticas
    print("\n4. Iniciando extracción con traducciones automáticas...")
    
    payload = {
        "tmx_id": tmx_id,
        "language": source_lang,
        "target_language": target_lang,  # CLAVE: incluir idioma destino
        "use_termsuite": True
    }
    
    print(f"   Payload: {json.dumps(payload, indent=2)}")
    
    try:
        response = requests.post(
            f"{API_BASE}/api/extract-tmx-language",
            headers={'Content-Type': 'application/json'},
            json=payload
        )
        
        if response.ok:
            extract_data = response.json()
            print(f"   Respuesta exitosa:")
            print(f"   - Total términos: {extract_data.get('total_terms', 'N/A')}")
            print(f"   - Translation Job ID: {extract_data.get('translation_job_id', 'N/A')}")
            print(f"   - Mensaje: {extract_data.get('message', 'N/A')}")
            
            # 5. Monitorear progreso de traducciones si hay job_id
            translation_job_id = extract_data.get('translation_job_id')
            if translation_job_id:
                print(f"\n5. Monitoreando progreso de traducciones (Job ID: {translation_job_id})...")
                
                for i in range(30):  # Máximo 30 intentos (5 minutos)
                    try:
                        status_response = requests.get(f"{API_BASE}/api/status/{translation_job_id}")
                        if status_response.ok:
                            status_data = status_response.json()
                            status = status_data.get('status')
                            progress = status_data.get('progress', 0)
                            message = status_data.get('message', '')
                            
                            print(f"   [{i+1:2d}] Estado: {status} | Progreso: {progress}% | {message}")
                            
                            if status == 'completed':
                                print("   ✅ Traducciones automáticas completadas!")
                                break
                            elif status == 'failed':
                                error = status_data.get('error', 'Error desconocido')
                                print(f"   ❌ Traducciones fallaron: {error}")
                                break
                        else:
                            print(f"   Error obteniendo estado: {status_response.text}")
                            break
                            
                    except Exception as e:
                        print(f"   Error monitoreando: {e}")
                        break
                    
                    time.sleep(10)  # Esperar 10 segundos
                else:
                    print("   ⏰ Timeout monitoreando traducciones")
            else:
                print("\n5. ❌ No se inició trabajo de traducción automática")
                print("   Posibles causas:")
                print("   - Ollama no disponible")
                print("   - No se envió target_language")
                print("   - Error en el backend")
        else:
            print(f"   ❌ Error en extracción: {response.status_code}")
            print(f"   Respuesta: {response.text}")
            
    except Exception as e:
        print(f"   Error: {e}")
        return
    
    # 6. Verificar si hay datos pre-procesados
    print("\n6. Verificando datos pre-procesados...")
    try:
        status_response = requests.get(f"{API_BASE}/api/tmx/{tmx_id}/translation-status")
        if status_response.ok:
            status_data = status_response.json()
            translations_ready = status_data.get('translations_ready', False)
            print(f"   Traducciones listas: {translations_ready}")
            
            if translations_ready:
                print(f"   - Total términos: {status_data.get('total_terms', 'N/A')}")
                print(f"   - Traducciones Ollama: {status_data.get('ollama_translations', 'N/A')}")
                print(f"   - Procesado en: {status_data.get('processed_at', 'N/A')}")
                print("   ✅ El flujo de traducciones automáticas funcionó correctamente!")
            else:
                in_progress = status_data.get('in_progress', False)
                if in_progress:
                    print(f"   - En progreso: {status_data.get('progress', 0)}%")
                    print(f"   - Mensaje: {status_data.get('message', 'N/A')}")
                else:
                    print("   - No se han iniciado traducciones automáticas")
        else:
            print(f"   Error verificando estado: {status_response.text}")
    except Exception as e:
        print(f"   Error: {e}")
    
    print("\n=== FIN DEL DEBUG ===")

if __name__ == "__main__":
    test_automatic_translation_flow()