#!/usr/bin/env python3
"""
Script de diagnóstico para verificar qué términos se extraen del TMX
"""

import sys
import os
from pathlib import Path

# Agregar el directorio app al path
sys.path.insert(0, 'app')

from services.tmx_parser import TMXParser

def debug_tmx(tmx_path: str, search_terms: list = None):
    """
    Diagnosticar extracción de términos de un TMX
    
    Args:
        tmx_path: Ruta al archivo TMX
        search_terms: Lista de términos a buscar específicamente
    """
    parser = TMXParser()
    
    print("=" * 80)
    print("DIAGNÓSTICO DE TMX")
    print("=" * 80)
    print(f"Archivo: {tmx_path}")
    print()
    
    # 1. Obtener idiomas disponibles
    print("1. IDIOMAS DISPONIBLES:")
    print("-" * 80)
    try:
        languages = parser.get_available_languages(tmx_path)
        print(f"   Idiomas detectados: {', '.join(languages)}")
    except Exception as e:
        print(f"   ✗ Error: {e}")
        return
    print()
    
    # 2. Extraer términos por idioma
    for lang in languages:
        print(f"2. TÉRMINOS EN IDIOMA '{lang.upper()}':")
        print("-" * 80)
        
        try:
            # Extraer términos únicos
            terms = parser.parse(tmx_path, language=lang)
            print(f"   Total términos únicos: {len(terms)}")
            
            # Extraer con frecuencias
            terms_freq = parser.parse_with_frequency(tmx_path, language=lang)
            total_occurrences = sum(terms_freq.values())
            print(f"   Total ocurrencias: {total_occurrences}")
            
            # Buscar términos específicos
            if search_terms:
                print(f"\n   Búsqueda de términos específicos:")
                for search_term in search_terms:
                    search_lower = search_term.lower()
                    
                    # Búsqueda exacta
                    if search_term in terms:
                        freq = terms_freq.get(search_term, 0)
                        print(f"   ✓ '{search_term}' encontrado (frecuencia: {freq})")
                    else:
                        # Búsqueda parcial (case-insensitive)
                        matches = [t for t in terms if search_lower in t.lower()]
                        if matches:
                            print(f"   ~ '{search_term}' no encontrado exactamente, pero hay coincidencias parciales:")
                            for match in matches[:5]:  # Mostrar máximo 5
                                freq = terms_freq.get(match, 0)
                                print(f"      - '{match}' (frecuencia: {freq})")
                        else:
                            print(f"   ✗ '{search_term}' NO encontrado")
            
            # Mostrar top 10 términos más frecuentes
            print(f"\n   Top 10 términos más frecuentes:")
            sorted_terms = sorted(terms_freq.items(), key=lambda x: x[1], reverse=True)[:10]
            for idx, (term, freq) in enumerate(sorted_terms, 1):
                # Truncar términos muy largos
                display_term = term if len(term) <= 50 else term[:47] + "..."
                print(f"      {idx:2d}. {display_term:50s} (freq: {freq})")
            
        except Exception as e:
            print(f"   ✗ Error al extraer términos: {e}")
        
        print()
    
    # 3. Verificar traducciones
    if len(languages) >= 2:
        print("3. VERIFICAR TRADUCCIONES:")
        print("-" * 80)
        source_lang = languages[0]
        target_lang = languages[1]
        
        try:
            translations = parser.parse_with_translations(
                tmx_path, 
                source_lang=source_lang,
                target_lang=target_lang
            )
            print(f"   Total pares de traducción ({source_lang} → {target_lang}): {len(translations)}")
            
            if search_terms:
                print(f"\n   Búsqueda de traducciones:")
                for search_term in search_terms:
                    search_lower = search_term.lower()
                    found = False
                    
                    for trans in translations:
                        if search_lower in trans['source'].lower():
                            print(f"   ✓ '{trans['source']}' → '{trans['target']}'")
                            found = True
                            break
                    
                    if not found:
                        print(f"   ✗ '{search_term}' no encontrado en traducciones")
            
            # Mostrar primeras 5 traducciones
            print(f"\n   Primeras 5 traducciones:")
            for idx, trans in enumerate(translations[:5], 1):
                source_display = trans['source'] if len(trans['source']) <= 40 else trans['source'][:37] + "..."
                target_display = trans['target'] if len(trans['target']) <= 40 else trans['target'][:37] + "..."
                print(f"      {idx}. {source_display:40s} → {target_display}")
                
        except Exception as e:
            print(f"   ✗ Error al extraer traducciones: {e}")
        
        print()
    
    print("=" * 80)
    print("FIN DEL DIAGNÓSTICO")
    print("=" * 80)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python debug_tmx.py <ruta_tmx> [término1] [término2] ...")
        print()
        print("Ejemplo:")
        print("  python debug_tmx.py uploads/tmx/abc123.tmx coupling \"mechanical adjustments\"")
        sys.exit(1)
    
    tmx_path = sys.argv[1]
    search_terms = sys.argv[2:] if len(sys.argv) > 2 else None
    
    if not os.path.exists(tmx_path):
        print(f"✗ Error: El archivo '{tmx_path}' no existe")
        sys.exit(1)
    
    debug_tmx(tmx_path, search_terms)
