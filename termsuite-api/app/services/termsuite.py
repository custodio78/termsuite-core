import subprocess
import os
import shlex
from pathlib import Path


class TermSuiteService:
    """Servicio para ejecutar TermSuite JAR"""
    
    def __init__(self):
        self.jar_path = os.getenv(
            'TERMSUITE_JAR', 
            '/app/termsuite/termsuite-core-3.0.10.jar'
        )
        self.treetagger_home = os.getenv('TREETAGGER_HOME', '/app/treetagger')
        # Opciones de memoria para Java (los permisos de módulos se configuran en JAVA_TOOL_OPTIONS)
        self.java_opts = os.getenv('JAVA_OPTS', '-Xms1g -Xmx4g')
    
    def extract_terms(
        self, 
        corpus_path: str, 
        output_path: str, 
        language: str = 'en',
        min_frequency: int = 2
    ):
        """
        Ejecutar TermSuite para extraer términos
        
        Args:
            corpus_path: Ruta al corpus
            output_path: Ruta de salida JSON
            language: Idioma (en, es, fr, de, etc.)
            min_frequency: Frecuencia mínima
        """
        if not Path(self.jar_path).exists():
            raise FileNotFoundError(
                f"TermSuite JAR no encontrado en: {self.jar_path}"
            )
        
        # Verificar que TreeTagger está instalado
        treetagger_path = Path(self.treetagger_home)
        if not treetagger_path.exists():
            raise FileNotFoundError(
                f"TreeTagger no encontrado en: {self.treetagger_home}\n"
                f"TermSuite requiere TreeTagger para funcionar.\n"
                f"Ver INSTALL_TREETAGGER.md para instrucciones de instalación."
            )
        
        # Verificar que el corpus existe
        corpus_path_obj = Path(corpus_path)
        if not corpus_path_obj.exists():
            raise FileNotFoundError(f"Corpus no encontrado en: {corpus_path}")
        
        # Verificar que hay archivos .txt en el corpus
        if corpus_path_obj.is_dir():
            txt_files = list(corpus_path_obj.glob('*.txt'))
            if not txt_files:
                raise FileNotFoundError(f"No se encontraron archivos .txt en: {corpus_path}")
            print(f"DEBUG: Encontrados {len(txt_files)} archivos .txt en el corpus")
        
        # Construir comando
        # TermSuite requiere TreeTagger (-t) y corpus de texto
        # Incluir JAXB en el classpath para Java 17
        # Usar TSV en lugar de JSON porque JSON no funciona en esta versión
        tsv_output = str(output_path).replace('.json', '.tsv')
        cmd = [
            'java',
            *shlex.split(self.java_opts),
            '-cp', '/app/lib/*:' + self.jar_path,
            'fr.univnantes.termsuite.tools.TerminologyExtractorCLI',
            '-t', self.treetagger_home,
            '--from-text-corpus', str(corpus_path),
            '--encoding', 'UTF-8',
            '-l', language,
            '--tsv', tsv_output,
            '--tsv-properties', 'pilot,rank,freq,spec,dfreq',
            '--post-filter-property', 'freq',
            '--post-filter-th', str(min_frequency),
            '--info'
        ]
        
        print(f"DEBUG: Ejecutando comando: {' '.join(cmd)}")
        
        # Ejecutar
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True,
                timeout=600  # 10 minutos timeout
            )
            print(f"DEBUG: TermSuite stdout:\n{result.stdout}")
            print(f"DEBUG: TermSuite stderr:\n{result.stderr}")
            
            # Convertir TSV a JSON
            if Path(tsv_output).exists():
                print(f"DEBUG: Convirtiendo TSV a JSON: {tsv_output} -> {output_path}")
                self._convert_tsv_to_json(tsv_output, output_path)
            else:
                print(f"WARNING: Archivo TSV no encontrado: {tsv_output}")
            
            return result.stdout
        except subprocess.CalledProcessError as e:
            print(f"ERROR: TermSuite failed with stderr:\n{e.stderr}")
            print(f"ERROR: TermSuite failed with stdout:\n{e.stdout}")
            raise Exception(f"Error ejecutando TermSuite: {e.stderr}")
        except subprocess.TimeoutExpired:
            raise Exception("TermSuite excedió el tiempo límite de ejecución")
    
    def _convert_tsv_to_json(self, tsv_path: str, json_path: str):
        """Convertir archivo TSV de TermSuite a formato JSON"""
        import csv
        import json
        
        terms = []
        with open(tsv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f, delimiter='\t')
            for row in reader:
                term_obj = {
                    "groupingKey": row.get('pilot', ''),
                    "frequency": int(row.get('freq', 0)) if row.get('freq') else 0,
                    "rank": int(row.get('rank', 0)) if row.get('rank') else 0,
                    "specificity": float(row.get('spec', 0)) if row.get('spec') else 0,
                    "documentFrequency": int(row.get('dfreq', 0)) if row.get('dfreq') else 0
                }
                terms.append(term_obj)
        
        output = {"terms": terms}
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(output, f, ensure_ascii=False, indent=2)
        
        print(f"DEBUG: Convertidos {len(terms)} términos de TSV a JSON")
