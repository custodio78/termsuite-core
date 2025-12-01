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
        # TermSuite requiere --from-text-corpus con encoding para corpus de texto plano
        cmd = [
            'java',
            *shlex.split(self.java_opts),
            '-jar', self.jar_path,
            '--from-text-corpus', str(corpus_path),
            '--encoding', 'UTF-8',
            '-l', language,
            '--json', str(output_path),
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
            return result.stdout
        except subprocess.CalledProcessError as e:
            raise Exception(f"Error ejecutando TermSuite: {e.stderr}")
        except subprocess.TimeoutExpired:
            raise Exception("TermSuite excedió el tiempo límite de ejecución")
