#!/usr/bin/env python3
"""
Script de prueba para verificar la limpieza de términos
"""

import sys
sys.path.insert(0, 'app')

from services.tmx_parser import TMXParser

# Crear instancia del parser
parser = TMXParser()

# Casos de prueba
test_cases = [
    ("a) elevador", "elevador"),
    ("b) sistema hidráulico", "sistema hidráulico"),
    ("1. plataforma", "plataforma"),
    ("2. motor eléctrico", "motor eléctrico"),
    ("1- válvula", "válvula"),
    ("2- bomba", "bomba"),
    ("- cilindro", "cilindro"),
    ("• pistón", "pistón"),
    ("* engranaje", "engranaje"),
    ("· rodamiento", "rodamiento"),
    ("A) Componente", "Componente"),
    ("3) tornillo", "tornillo"),
    ("  a)  espacio extra  ", "espacio extra"),
    ("normal sin bullet", "normal sin bullet"),
    ("", ""),
]

print("=" * 60)
print("PRUEBA DE LIMPIEZA DE TÉRMINOS")
print("=" * 60)

all_passed = True
for original, expected in test_cases:
    cleaned = parser._clean_term(original)
    status = "✓" if cleaned == expected else "✗"
    
    if cleaned != expected:
        all_passed = False
        print(f"\n{status} FALLO:")
        print(f"  Original:  '{original}'")
        print(f"  Esperado:  '{expected}'")
        print(f"  Obtenido:  '{cleaned}'")
    else:
        print(f"{status} '{original}' → '{cleaned}'")

print("\n" + "=" * 60)
if all_passed:
    print("✓ TODAS LAS PRUEBAS PASARON")
else:
    print("✗ ALGUNAS PRUEBAS FALLARON")
print("=" * 60)
