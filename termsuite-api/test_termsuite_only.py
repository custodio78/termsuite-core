#!/usr/bin/env python3
"""
Script para probar solo la extracción con TermSuite
"""

import requests
from pathlib import Path

API_BASE = "http://localhost:7000"
TMX_FILE = "examples/test_multiple_translations.tmx"

print("=" * 80)
print("PRUEBA DE EXTRACCIÓN CON TERMSUITE")
print("=" * 80)

# 1. Subir TMX
print("\n1. Subiendo TMX con segmentos completos...")
with open(TMX_FILE, 'rb') as f:
    files = {'file': (Path(TMX_FILE).name, f, 'application/xml')}
    response = requests.post(f"{API_BASE}/api/upload-tmx", files=files)

if response.status_code != 200:
    print(f"✗ Error al subir TMX: {response.text}")
    exit(1)

data = response.json()
tmx_id = data['file_id']
print(f"✓ TMX subido: {tmx_id}")
print(f"  Mensaje: {data['message']}")

# 2. Extraer con TermSuite
print("\n2. Extrayendo términos con TermSuite...")
print("   (Esto puede tardar 30-60 segundos...)")
print("   Nota: Usando idioma 'en' porque solo tenemos el modelo de inglés")

response = requests.post(
    f"{API_BASE}/api/extract-tmx-language",
    params={
        'tmx_id': tmx_id,
        'language': 'en',  # Cambiar a inglés porque tenemos el modelo
        'target_language': 'es',
        'use_termsuite': True
    },
    timeout=120
)

if response.status_code != 200:
    print(f"✗ Error: {response.text}")
    exit(1)

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
    exit(1)

output_file = f"test_termsuite_{tmx_id}.xlsx"
with open(output_file, 'wb') as f:
    f.write(response.content)

print(f"✓ Excel exportado: {output_file}")
print(f"  Tamaño: {len(response.content)} bytes")

# 4. Verificar contenido
try:
    import pandas as pd
    df = pd.read_excel(output_file)
    print(f"\n4. Términos extraídos con TermSuite:")
    print(f"   Total: {len(df)} términos")
    
    print("\n   Top 15 términos:")
    for idx, row in df.head(15).iterrows():
        term = row.get('Término', '')
        freq = row.get('Frecuencia', 0)
        words = row.get('Palabras', 0)
        print(f"     {idx+1:2d}. {term:30s} ({freq}x, {words} palabras)")
    
except ImportError:
    print("  ⚠ pandas no disponible")
except Exception as e:
    print(f"  ⚠ Error al leer Excel: {e}")

print("\n" + "=" * 80)
print("✓ PRUEBA COMPLETADA")
print("=" * 80)
