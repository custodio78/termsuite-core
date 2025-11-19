import subprocess
import os
from pathlib import Path


class TermSuiteService:
    """Servicio para ejecutar TermSuite JAR"""
    
    def __init__(self):
        self.jar_path = os.getenv(
            'TERMSUITE_JAR', 
            '/app/termsuite/termsuite-core-3.0.10.jar'
        )
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
        
        # Construir comando
        cmd = [
            'java',
            *self.java_opts.split(),
            '-jar', self.jar_path,
            '-c', corpus_path,
            '-l', language,
            '--json', output_path,
            '--post-filter-property', 'freq',
            '--post-filter-th', str(min_frequency),
            '--info'
        ]
        
        # Ejecutar
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True,
                timeout=600  # 10 minutos timeout
            )
            return result.stdout
        except subprocess.CalledProcessError as e:
            raise Exception(f"Error ejecutando TermSuite: {e.stderr}")
        except subprocess.TimeoutExpired:
            raise Exception("TermSuite excedió el tiempo límite de ejecución")
