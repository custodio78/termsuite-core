#!/usr/bin/env python3
"""
Verificar contenido del Excel generado
"""

import pandas as pd
import sys

def check_excel_content():
    """Verificar contenido del Excel"""
    
    filename = "test_export_fe41b5d2-4fe0-4432-b02e-e5d1b54454ed.xlsx"
    
    try:
        # Leer Excel
        df = pd.read_excel(filename)
        
        print(f"=== Contenido del Excel: {filename} ===")
        print(f"Filas: {len(df)}")
        print(f"Columnas: {list(df.columns)}")
        
        # Mostrar primeras filas
        print(f"\nPrimeras 10 filas:")
        print(df.head(10).to_string())
        
        # Verificar traducciones
        if 'Traducción' in df.columns:
            translations_count = df['Traducción'].notna().sum()
            empty_translations = df['Traducción'].isna().sum()
            
            print(f"\n=== Estadísticas de Traducciones ===")
            print(f"Términos con traducción: {translations_count}")
            print(f"Términos sin traducción: {empty_translations}")
            
            # Verificar Ollama
            if 'Ollama' in df.columns:
                ollama_yes = (df['Ollama'] == 'Sí').sum()
                ollama_no = (df['Ollama'] == 'No necesario').sum()
                ollama_error = (df['Ollama'] == 'Error').sum()
                
                print(f"\n=== Estadísticas de Ollama ===")
                print(f"Traducciones Ollama exitosas: {ollama_yes}")
                print(f"Ollama no necesario: {ollama_no}")
                print(f"Errores Ollama: {ollama_error}")
                
                # Mostrar ejemplos de traducciones Ollama
                ollama_examples = df[df['Ollama'] == 'Sí'].head(5)
                if not ollama_examples.empty:
                    print(f"\n=== Ejemplos de Traducciones Ollama ===")
                    for idx, row in ollama_examples.iterrows():
                        print(f"\nTérmino: {row['Término']}")
                        print(f"Tipo Match: {row.get('Tipo Match', 'N/A')}")
                        print(f"Traducción: {row['Traducción'][:200]}...")
            
            # Verificar tipos de match
            if 'Tipo Match' in df.columns:
                match_counts = df['Tipo Match'].value_counts()
                print(f"\n=== Tipos de Match ===")
                for match_type, count in match_counts.items():
                    print(f"{match_type}: {count}")
        
        else:
            print("❌ No se encontró columna 'Traducción'")
            
    except Exception as e:
        print(f"❌ Error leyendo Excel: {e}")

if __name__ == "__main__":
    check_excel_content()