#!/usr/bin/env python3
"""
Debug específico del endpoint asíncrono
"""

import requests
import time
import json

def debug_async_export():
    """Debug del endpoint asíncrono paso a paso"""
    
    base_url = "http://localhost:7000"
    tmx_id = "fe41b5d2-4fe0-4432-b02e-e5d1b54454ed"
    
    print("=== Debug Async Export ===")
    
    # 1. Verificar términos cargados
    print("\n1. Verificando términos cargados...")
    try:
        response = requests.get(f"{base_url}/api/tmx-debug/{tmx_id}")
        if response.status_code == 200:
            debug_data = response.json()
            print(f"Idiomas: {debug_data['languages']}")
            for lang, details in debug_data['details'].items():
                print(f"  {lang}: {details['total_unique_terms']} términos únicos")
        else:
            print(f"❌ Error: {response.status_code}")
            return
    except Exception as e:
        print(f"❌ Error: {e}")
        return
    
    # 2. Iniciar exportación con parámetros específicos
    print(f"\n2. Iniciando exportación con debug...")
    export_params = {
        'min_frequency': 1,
        'top_n': 10,  # Solo 10 términos para debug rápido
        'include_translation': True,
        'use_ollama': True
    }
    
    try:
        response = requests.post(f"{base_url}/api/export/tmx-excel-async/{tmx_id}", params=export_params)
        if response.status_code == 200:
            export_data = response.json()
            export_job_id = export_data['export_job_id']
            print(f"✅ Job ID: {export_job_id}")
        else:
            print(f"❌ Error: {response.status_code} - {response.text}")
            return
    except Exception as e:
        print(f"❌ Error: {e}")
        return
    
    # 3. Monitorear con detalle
    print(f"\n3. Monitoreando progreso detallado...")
    max_attempts = 30
    attempt = 0
    
    while attempt < max_attempts:
        try:
            response = requests.get(f"{base_url}/api/status/{export_job_id}")
            if response.status_code == 200:
                status_data = response.json()
                print(f"  [{attempt:2d}] {status_data['progress']:3d}% - {status_data['message']}")
                
                if status_data['status'] == 'completed':
                    print("✅ Completado!")
                    break
                elif status_data['status'] == 'failed':
                    print(f"❌ Falló: {status_data.get('error', 'Error desconocido')}")
                    return
            else:
                print(f"❌ Error status: {response.status_code}")
                return
                
        except Exception as e:
            print(f"❌ Error: {e}")
            return
        
        time.sleep(1)
        attempt += 1
    
    if attempt >= max_attempts:
        print("❌ Timeout")
        return
    
    # 4. Descargar y analizar resultado
    print(f"\n4. Descargando resultado...")
    try:
        response = requests.get(f"{base_url}/api/download/export/{export_job_id}")
        if response.status_code == 200:
            filename = f"debug_export_{export_job_id}.xlsx"
            with open(filename, 'wb') as f:
                f.write(response.content)
            print(f"✅ Descargado: {filename} ({len(response.content)} bytes)")
            
            # Analizar contenido
            import pandas as pd
            try:
                df = pd.read_excel(filename)
                print(f"\n5. Análisis del Excel:")
                print(f"   Filas: {len(df)}")
                print(f"   Columnas: {list(df.columns)}")
                
                if 'Traducción' in df.columns:
                    translations_count = df['Traducción'].notna().sum()
                    print(f"   Términos con traducción: {translations_count}")
                    
                    # Mostrar algunos ejemplos
                    translated = df[df['Traducción'].notna()].head(3)
                    if not translated.empty:
                        print(f"\n   Ejemplos de traducciones:")
                        for idx, row in translated.iterrows():
                            print(f"     {row['Término']} → {row['Traducción'][:100]}...")
                else:
                    print("   ❌ No hay columna 'Traducción'")
                    
            except Exception as e:
                print(f"   ❌ Error leyendo Excel: {e}")
        else:
            print(f"❌ Error descarga: {response.status_code}")
            return
    except Exception as e:
        print(f"❌ Error: {e}")
        return
    
    print("\n=== Debug Completado ===")

if __name__ == "__main__":
    debug_async_export()