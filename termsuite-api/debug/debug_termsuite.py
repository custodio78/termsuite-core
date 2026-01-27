#!/usr/bin/env python3
"""
Debug específico de TermSuite
"""

import requests
import json

def debug_termsuite():
    """Debug de TermSuite paso a paso"""
    
    base_url = "http://localhost:7000"
    tmx_id = "d8828360-3f32-49bc-bbe2-ef1617e4c94b"
    
    print("=== Debug TermSuite ===")
    
    # 1. Verificar que el TMX tiene contenido
    print("\n1. Verificando contenido del TMX...")
    try:
        response = requests.get(f"{base_url}/api/tmx-debug/{tmx_id}")
        if response.status_code == 200:
            debug_data = response.json()
            print(f"Idiomas: {debug_data['languages']}")
            
            # Usar español que sabemos que tiene contenido
            if 'es' in debug_data['languages']:
                lang_details = debug_data['details']['es']
                print(f"Español: {lang_details['total_unique_terms']} términos únicos")
                print(f"Primeros 3 términos:")
                for term, freq in lang_details['top_10'][:3]:
                    print(f"  - '{term}' ({freq}x)")
            else:
                print("❌ No hay español en el TMX")
                return
        else:
            print(f"❌ Error: {response.status_code}")
            return
    except Exception as e:
        print(f"❌ Error: {e}")
        return
    
    # 2. Probar extracción con TermSuite usando español
    print(f"\n2. Probando extracción TermSuite con español...")
    try:
        extract_params = {
            'tmx_id': tmx_id,
            'language': 'es',  # Usar español
            'target_language': 'en',
            'use_termsuite': True
        }
        
        response = requests.post(f"{base_url}/api/extract-tmx-language", params=extract_params)
        if response.status_code == 200:
            extract_result = response.json()
            print(f"✅ Resultado: {extract_result['message']}")
            
            # Verificar si se crearon archivos
            print(f"\n3. Verificando archivos generados...")
            
            # Verificar términos procesados
            response2 = requests.get(f"{base_url}/api/tmx-debug/{tmx_id}?search=test")
            if response2.status_code == 200:
                debug_data2 = response2.json()
                print(f"Debug después de extracción: {debug_data2}")
        else:
            print(f"❌ Error extracción: {response.status_code} - {response.text}")
            
            # Si falla, probar sin TermSuite para comparar
            print(f"\n3. Probando SIN TermSuite para comparar...")
            extract_params['use_termsuite'] = False
            
            response3 = requests.post(f"{base_url}/api/extract-tmx-language", params=extract_params)
            if response3.status_code == 200:
                extract_result3 = response3.json()
                print(f"✅ Sin TermSuite: {extract_result3['message']}")
            else:
                print(f"❌ Error sin TermSuite: {response3.status_code} - {response3.text}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print(f"\n=== Debug Completado ===")

if __name__ == "__main__":
    debug_termsuite()