#!/usr/bin/env python3
"""
Script simple para verificar que el servidor está funcionando
"""

import requests

API_BASE = "http://localhost:7000"

print("Verificando servidor...")
print(f"URL: {API_BASE}")

try:
    response = requests.get(f"{API_BASE}/api", timeout=5)
    
    if response.status_code == 200:
        data = response.json()
        print("\n✓ Servidor funcionando correctamente")
        print(f"  Versión: {data.get('version', 'N/A')}")
        print(f"  Endpoints disponibles:")
        for name, path in data.get('endpoints', {}).items():
            print(f"    - {name}: {path}")
    else:
        print(f"\n✗ Servidor respondió con código: {response.status_code}")
        
except requests.exceptions.ConnectionError:
    print("\n✗ No se puede conectar al servidor")
    print("  Verifica que Docker está corriendo:")
    print("  - docker ps")
    print("  - docker logs termsuite-api")
    
except Exception as e:
    print(f"\n✗ Error: {e}")
