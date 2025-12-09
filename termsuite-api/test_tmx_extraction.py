#!/usr/bin/env python3
"""
Script de prueba para verificar la extracción de términos del TMX
"""

import requests
import json
import time
from pathlib import Path

# Configuración
API_BASE = "http://localhost:7000"
TMX_FILE = "examples/test_terms_glossary.tmx"

def test_tmx_extraction():
    """Probar extracción completa de TMX"""
    
    print("=" * 80)
    print("PRUEBA DE EXTRACCIÓN TMX")
    print("=" * 80)
    
    # 1. Subir TMX
    print("\n1. Subiendo TMX...")
    with open(TMX_FILE, 'rb') as f:
        files = {'file': (Path(TMX_FILE).name, f, 'application/xml')}
        response = requests.post(f"{API_BASE}/api/upload-tmx", files=files)
    
    if response.status_code != 200:
        print(f"✗ Error al subir TMX: {response.text}")
        return
    
    data = response.json()
    tmx_id = data['file_id']
    print(f"✓ TMX subido: {tmx_id}")
    print(f"  Mensaje: {data['message']}")
    
    # 2. Obtener idiomas disponibles
    print("\n2. Obteniendo idiomas disponibles...")
    response = requests.get(f"{API_BASE}/api/tmx-languages/{tmx_id}")
    
    if response.status_code != 200:
        print(f"✗ Error: {response.text}")
        return
    
    data = response.json()
    languages = data['available_languages']
    print(f"✓ Idiomas detectados: {', '.join(languages)}")
    
    # 3. Extraer términos (modo directo)
    print("\n3. Extrayendo términos (modo directo)...")
    response = requests.post(
        f"{API_BASE}/api/extract-tmx-language",
        params={
            'tmx_id': tmx_id,
            'language': 'es',
            'target_language': 'en',
            'use_termsuite': False
        }
    )
    
    if response.status_code != 200:
        print(f"✗ Error: {response.text}")
        return
    
    data = response.json()
    print(f"✓ {data['message']}")
    print(f"  Total términos: {data['total_terms']}")
    print(f"  Modo: {data['extraction_mode']}")
    
    # 4. Buscar término específico
    print("\n4. Buscando término 'válvula'...")
    response = requests.get(
        f"{API_BASE}/api/tmx-debug/{tmx_id}",
        params={'search': 'válvula'}
    )
    
    if response.status_code != 200:
        print(f"✗ Error: {response.text}")
        return
    
    data = response.json()
    for lang, info in data['details'].items():
        if 'search' in info:
            search_info = info['search']
            if search_info['exact_match']:
                print(f"✓ {lang.upper()}: Encontrado (frecuencia: {search_info['frequency']})")
            else:
                print(f"✗ {lang.upper()}: No encontrado")
    
    # 5. Exportar a Excel
    print("\n5. Exportando a Excel...")
    response = requests.get(
        f"{API_BASE}/api/export/tmx-excel/{tmx_id}",
        params={
            'min_frequency': 1,
            'include_translation': True,
            'format': 'excel'
        }
    )
    
    if response.status_code != 200:
        print(f"✗ Error: {response.text}")
        return
    
    # Guardar Excel
    output_file = f"test_output_{tmx_id}.xlsx"
    with open(output_file, 'wb') as f:
        f.write(response.content)
    
    print(f"✓ Excel exportado: {output_file}")
    print(f"  Tamaño: {len(response.content)} bytes")
    
    # 6. Verificar contenido del Excel
    print("\n6. Verificando contenido del Excel...")
    try:
        import pandas as pd
        df = pd.read_excel(output_file)
        print(f"✓ Excel leído correctamente")
        print(f"  Filas: {len(df)}")
        print(f"  Columnas: {', '.join(df.columns)}")
        
        # Mostrar primeros 5 términos
        print("\n  Primeros 5 términos:")
        for idx, row in df.head(5).iterrows():
            term = row.get('Término', '')
            freq = row.get('Frecuencia', 0)
            trans = row.get('Traducción', '')
            variants = row.get('Variantes', 0)
            print(f"    {idx+1}. {term} ({freq}x) → {trans} [{variants} variantes]")
        
        # Verificar términos con múltiples traducciones
        print("\n  Términos con múltiples traducciones:")
        multi_trans = df[df.get('Variantes', 0) > 1]
        for idx, row in multi_trans.iterrows():
            term = row.get('Término', '')
            trans = row.get('Traducción', '')
            variants = row.get('Variantes', 0)
            print(f"    - {term} → {trans} [{variants} variantes]")
        
    except ImportError:
        print("  ⚠ pandas no disponible, saltando verificación de contenido")
    except Exception as e:
        print(f"  ⚠ Error al leer Excel: {e}")
    
    print("\n" + "=" * 80)
    print("✓ PRUEBA COMPLETADA EXITOSAMENTE")
    print("=" * 80)


def test_tmx_with_termsuite():
    """Probar extracción con TermSuite"""
    
    print("\n" + "=" * 80)
    print("PRUEBA DE EXTRACCIÓN CON TERMSUITE")
    print("=" * 80)
    
    # Usar el TMX con segmentos completos
    tmx_file = "examples/test_multiple_translations.tmx"
    
    # 1. Subir TMX
    print("\n1. Subiendo TMX con segmentos completos...")
    with open(tmx_file, 'rb') as f:
        files = {'file': (Path(tmx_file).name, f, 'application/xml')}
        response = requests.post(f"{API_BASE}/api/upload-tmx", files=files)
    
    if response.status_code != 200:
        print(f"✗ Error al subir TMX: {response.text}")
        return
    
    data = response.json()
    tmx_id = data['file_id']
    print(f"✓ TMX subido: {tmx_id}")
    
    # 2. Extraer con TermSuite
    print("\n2. Extrayendo términos con TermSuite...")
    print("   (Esto puede tardar unos segundos...)")
    
    response = requests.post(
        f"{API_BASE}/api/extract-tmx-language",
        params={
            'tmx_id': tmx_id,
            'language': 'es',
            'target_language': 'en',
            'use_termsuite': True
        }
    )
    
    if response.status_code != 200:
        print(f"✗ Error: {response.text}")
        return
    
    data = response.json()
    print(f"✓ {data['message']}")
    print(f"  Total términos extraídos: {data['total_terms']}")
    print(f"  Modo: {data['extraction_mode']}")
    
    # 3. Exportar
    print("\n3. Exportando resultados...")
    response = requests.get(
        f"{API_BASE}/api/export/tmx-excel/{tmx_id}",
        params={
            'min_frequency': 1,
            'include_translation': True,
            'format': 'excel'
        }
    )
    
    if response.status_code != 200:
        print(f"✗ Error: {response.text}")
        return
    
    output_file = f"test_termsuite_{tmx_id}.xlsx"
    with open(output_file, 'wb') as f:
        f.write(response.content)
    
    print(f"✓ Excel exportado: {output_file}")
    
    # 4. Verificar contenido
    try:
        import pandas as pd
        df = pd.read_excel(output_file)
        print(f"\n4. Términos extraídos con TermSuite:")
        print(f"   Total: {len(df)} términos")
        
        print("\n   Top 10 términos:")
        for idx, row in df.head(10).iterrows():
            term = row.get('Término', '')
            freq = row.get('Frecuencia', 0)
            print(f"     {idx+1}. {term} ({freq}x)")
        
    except Exception as e:
        print(f"  ⚠ Error al leer Excel: {e}")
    
    print("\n" + "=" * 80)
    print("✓ PRUEBA CON TERMSUITE COMPLETADA")
    print("=" * 80)


if __name__ == "__main__":
    try:
        # Verificar que el servidor está corriendo
        response = requests.get(f"{API_BASE}/api")
        if response.status_code != 200:
            print("✗ El servidor no está respondiendo")
            print("  Asegúrate de que el Docker está corriendo en http://localhost:8000")
            exit(1)
        
        # Ejecutar pruebas
        test_tmx_extraction()
        
        # Preguntar si quiere probar con TermSuite
        print("\n¿Deseas probar la extracción con TermSuite? (s/n): ", end='')
        if input().lower() == 's':
            test_tmx_with_termsuite()
        
    except requests.exceptions.ConnectionError:
        print("✗ No se puede conectar al servidor")
        print("  Asegúrate de que el Docker está corriendo en http://localhost:8000")
    except KeyboardInterrupt:
        print("\n\nPrueba interrumpida por el usuario")
    except Exception as e:
        print(f"\n✗ Error inesperado: {e}")
        import traceback
        traceback.print_exc()
