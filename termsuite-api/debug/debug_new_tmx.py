#!/usr/bin/env python3
"""
Debug del TMX recién subido
"""

import requests
import json

def debug_new_tmx():
    """Debug del TMX que acabas de subir"""
    
    base_url = "http://localhost:7000"
    tmx_id = "d8828360-3f32-49bc-bbe2-ef1617e4c94b"  # Del log
    
    print(f"=== Debug TMX: {tmx_id} ===")
    
    # 1. Verificar información del TMX
    print("\n1. Información del TMX:")
    try:
        response = requests.get(f"{base_url}/api/tmx-debug/{tmx_id}")
        if response.status_code == 200:
            debug_data = response.json()
            print(f"Idiomas disponibles: {debug_data['languages']}")
            
            for lang, details in debug_data['details'].items():
                print(f"\n  {lang.upper()}:")
                print(f"    Términos únicos: {details['total_unique_terms']}")
                print(f"    Total ocurrencias: {details['total_occurrences']}")
                print(f"    Top 5 términos:")
                for term, freq in details['top_10'][:5]:
                    print(f"      - '{term}' ({freq}x)")
        else:
            print(f"❌ Error: {response.status_code} - {response.text}")
            return
    except Exception as e:
        print(f"❌ Error: {e}")
        return
    
    # 2. Verificar archivo de términos procesados
    print(f"\n2. Verificando términos procesados...")
    try:
        response = requests.get(f"{base_url}/api/tmx-languages/{tmx_id}")
        if response.status_code == 200:
            lang_data = response.json()
            print(f"Idiomas detectados: {lang_data['available_languages']}")
        else:
            print(f"❌ Error idiomas: {response.status_code}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # 3. Probar extracción CON TermSuite
    print(f"\n3. Probando extracción CON TermSuite...")
    try:
        # Usar el primer idioma disponible
        if debug_data['languages']:
            source_lang = debug_data['languages'][0]
            target_lang = debug_data['languages'][1] if len(debug_data['languages']) > 1 else debug_data['languages'][0]
            
            extract_url = f"{base_url}/api/extract-tmx-language"
            extract_params = {
                'tmx_id': tmx_id,
                'language': source_lang,
                'target_language': target_lang,
                'use_termsuite': True  # CON TermSuite
            }
            
            response = requests.post(extract_url, params=extract_params)
            if response.status_code == 200:
                extract_result = response.json()
                print(f"✅ Extracción con TermSuite: {extract_result['message']}")
                
                # Ahora probar exportación
                print(f"\n4. Probando exportación directa...")
                export_params = {
                    'min_frequency': 1,  # Frecuencia mínima 1
                    'top_n': 50,
                    'include_translation': True,
                    'use_ollama': True
                }
                
                response = requests.post(f"{base_url}/api/export/tmx-excel-async/{tmx_id}", params=export_params)
                if response.status_code == 200:
                    export_data = response.json()
                    print(f"✅ Exportación iniciada: {export_data['export_job_id']}")
                    
                    # Monitorear brevemente
                    import time
                    for i in range(10):
                        time.sleep(1)
                        status_response = requests.get(f"{base_url}/api/status/{export_data['export_job_id']}")
                        if status_response.status_code == 200:
                            status_data = status_response.json()
                            print(f"  [{i}] {status_data['progress']}% - {status_data['message']}")
                            
                            if status_data['status'] == 'completed':
                                print("✅ Exportación completada!")
                                break
                            elif status_data['status'] == 'failed':
                                print(f"❌ Exportación falló: {status_data.get('error')}")
                                break
                else:
                    print(f"❌ Error exportación: {response.status_code} - {response.text}")
            else:
                print(f"❌ Error extracción: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print(f"\n=== Debug Completado ===")

if __name__ == "__main__":
    debug_new_tmx()