import os
import requests
import json
from typing import List, Dict, Optional
import asyncio
import aiohttp
from pathlib import Path


class OllamaTranslator:
    """Servicio para traducir términos usando Ollama con optimizaciones"""
    
    def __init__(self):
        # Obtener servidor Ollama del .env o usar por defecto
        self.ollama_host = os.getenv('OLLAMA_HOST', '192.168.0.88')
        self.ollama_port = os.getenv('OLLAMA_PORT', '11434')
        self.base_url = f"http://{self.ollama_host}:{self.ollama_port}"
        self.model = os.getenv('OLLAMA_MODEL', 'llama3.2:latest')
        
        # Configuración de optimización
        self.cache_enabled = os.getenv('OLLAMA_CACHE_ENABLED', 'true').lower() == 'true'
        self.cache_dir = Path(os.getenv('DATA_DIR', '/app/data')) / 'ollama_cache'
        self.cache_dir.mkdir(exist_ok=True)
        
        # Caché en memoria para sesión actual
        self.memory_cache = {}
        
        # Configuración de rendimiento
        self.batch_size = int(os.getenv('OLLAMA_BATCH_SIZE', '5'))
        self.timeout = int(os.getenv('OLLAMA_TIMEOUT', '30'))
        self.max_retries = int(os.getenv('OLLAMA_MAX_RETRIES', '2'))
        
        # Callback para logging (se configura desde main.py)
        self.log_callback = None
        
    def is_available(self) -> bool:
        """Verificar si el servidor Ollama está disponible"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except Exception:
            return False
    
    def get_available_models(self) -> List[str]:
        """Obtener lista de modelos disponibles en Ollama"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=10)
            if response.status_code == 200:
                data = response.json()
                return [model['name'] for model in data.get('models', [])]
            return []
        except Exception:
            return []
    
    def _get_cache_key(self, term: str, source_lang: str, target_lang: str, context: str = None) -> str:
        """Generar clave única para caché"""
        import hashlib
        key_data = f"{term}|{source_lang}|{target_lang}|{context or ''}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def _get_cache_file_path(self, source_lang: str, target_lang: str) -> Path:
        """Obtener ruta del archivo de caché para un par de idiomas"""
        return self.cache_dir / f"translations_{source_lang}_{target_lang}.json"
    
    def _load_cache(self, source_lang: str, target_lang: str) -> dict:
        """Cargar caché desde archivo"""
        if not self.cache_enabled:
            return {}
        
        cache_file = self._get_cache_file_path(source_lang, target_lang)
        if cache_file.exists():
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading cache: {e}")
        return {}
    
    def _save_cache(self, cache_data: dict, source_lang: str, target_lang: str):
        """Guardar caché en archivo"""
        if not self.cache_enabled:
            return
        
        cache_file = self._get_cache_file_path(source_lang, target_lang)
        try:
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Error saving cache: {e}")
    
    def _get_from_cache(self, term: str, source_lang: str, target_lang: str, context: str = None) -> Optional[dict]:
        """Obtener traducción desde caché"""
        cache_key = self._get_cache_key(term, source_lang, target_lang, context)
        
        # Primero verificar caché en memoria
        if cache_key in self.memory_cache:
            return self.memory_cache[cache_key]
        
        # Luego verificar caché persistente
        cache_data = self._load_cache(source_lang, target_lang)
        if cache_key in cache_data:
            # Cargar en memoria para acceso rápido
            self.memory_cache[cache_key] = cache_data[cache_key]
            return cache_data[cache_key]
        
        return None
    
    def _save_to_cache(self, term: str, source_lang: str, target_lang: str, context: str, result: dict):
        """Guardar traducción en caché"""
        cache_key = self._get_cache_key(term, source_lang, target_lang, context)
        
        # Guardar en memoria
        self.memory_cache[cache_key] = result
        
        # Guardar en archivo
        cache_data = self._load_cache(source_lang, target_lang)
        cache_data[cache_key] = result
        self._save_cache(cache_data, source_lang, target_lang)
    
    def translate_term(self, term: str, source_lang: str, target_lang: str, context: str = None) -> Optional[dict]:
        """
        Traducir un término individual usando Ollama con caché y optimizaciones
        
        Args:
            term: Término a traducir
            source_lang: Idioma origen (es, en, fr, etc.)
            target_lang: Idioma destino
            context: Contexto adicional para mejorar la traducción
            
        Returns:
            Diccionario con traducción y contexto, o None si falla
        """
        # Log inicio
        if self.log_callback:
            self.log_callback("TRANSLATE_START", term, "INICIANDO", f"{source_lang} -> {target_lang}")
        
        # 1. Verificar caché primero
        cached_result = self._get_from_cache(term, source_lang, target_lang, context)
        if cached_result:
            if self.log_callback:
                self.log_callback("CACHE_HIT", term, "CACHE", f"Encontrado en caché: {cached_result['translation'][:30]}...")
            return cached_result
        
        # 2. Si no está en caché, traducir con reintentos
        if self.log_callback:
            self.log_callback("CACHE_MISS", term, "TRADUCIENDO", "No encontrado en caché, consultando Ollama...")
        
        for attempt in range(self.max_retries + 1):
            try:
                if self.log_callback and attempt > 0:
                    self.log_callback("RETRY", term, "REINTENTANDO", f"Intento {attempt + 1}/{self.max_retries + 1}")
                
                result = self._translate_with_ollama(term, source_lang, target_lang, context)
                if result:
                    # Guardar en caché
                    self._save_to_cache(term, source_lang, target_lang, context, result)
                    if self.log_callback:
                        self.log_callback("TRANSLATE_SUCCESS", term, "COMPLETADO", f"Traducido: {result['translation'][:30]}...")
                    return result
            except Exception as e:
                error_msg = str(e)
                if self.log_callback:
                    self.log_callback("TRANSLATE_ERROR", term, "ERROR", f"Intento {attempt + 1} falló: {error_msg[:50]}...")
                print(f"Attempt {attempt + 1} failed for '{term}': {error_msg}")
                if attempt < self.max_retries:
                    import time
                    time.sleep(1)  # Esperar 1 segundo antes del siguiente intento
        
        if self.log_callback:
            self.log_callback("TRANSLATE_FAILED", term, "FALLIDO", f"Falló después de {self.max_retries + 1} intentos")
        return None
    
    def _translate_with_ollama(self, term: str, source_lang: str, target_lang: str, context: str = None) -> Optional[dict]:
        """Realizar la traducción real con Ollama"""
        try:
            # Mapeo de códigos de idioma a nombres completos
            lang_names = {
                'es': 'Spanish',
                'en': 'English', 
                'fr': 'French',
                'de': 'German',
                'it': 'Italian',
                'pt': 'Portuguese',
                'ca': 'Catalan',
                'eu': 'Basque',
                'gl': 'Galician'
            }
            
            source_name = lang_names.get(source_lang, source_lang)
            target_name = lang_names.get(target_lang, target_lang)
            
            # Crear prompt para traducción técnica BASADA EN CONTEXTO TMX
            if context:
                prompt = f"""You are a professional technical translator. Translate the following term from {source_name} to {target_name} based STRICTLY on the provided TMX context.

Term to translate: "{term}"
Source language: {source_name}
Target language: {target_name}
TMX Context: {context}

CRITICAL Instructions:
- ONLY extract translations that literally appear in the TMX context provided above
- DO NOT add any translations that are not explicitly present in the context text
- DO NOT include the original term itself as a translation (e.g., don't translate "usuario" as "usuario")
- Look for exact matches or variations of the term in the target language within the context
- If multiple variations exist in the context, separate them with " | " (pipe symbol with spaces)
- Order from most frequent to least frequent in the context
- Respond with only the translated term(s) that you can find in the context text
- If the term does not appear translated in the context, respond with "NOT_FOUND"

Examples based on context:
- Context: "The user must protect..." Term: "usuario" → "user"
- Context: "end user protection" Term: "usuario" → "end user"
- Context: "The user and end user must..." Term: "usuario" → "user | end user"
- Context: "sistema de gestión" Term: "usuario" → "NOT_FOUND"

Translation:"""
            else:
                prompt = f"""You are a professional technical translator. Translate the following term from {source_name} to {target_name}.

Term to translate: "{term}"
Source language: {source_name}
Target language: {target_name}

Instructions:
- Provide the most accurate technical translation for this term
- If it's a technical term, preserve its technical meaning
- Provide up to 3 most relevant translations separated by " | " (pipe symbol with spaces)
- Order from most common to least common usage
- Respond with only the translated term(s), no explanations
- If the term is a proper noun or doesn't need translation, return it as is

Translation:"""
            
            # Log del prompt enviado
            if self.log_callback:
                self.log_callback("PROMPT_SENT", term, "ENVIANDO", f"Enviando prompt a Ollama...", prompt=prompt)
            
            # Hacer petición a Ollama
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.1,  # Baja temperatura para traducciones más consistentes
                    "top_p": 0.9,
                    "max_tokens": 50
                }
            }
            
            response = requests.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                raw_response = result.get('response', '').strip()
                
                # Log de la respuesta cruda
                if self.log_callback:
                    self.log_callback("RESPONSE_RECEIVED", term, "RESPUESTA", f"Respuesta cruda recibida", response=raw_response)
                
                # Limpiar la respuesta
                translation = self._clean_translation(raw_response)
                
                # Log de la respuesta limpia
                if self.log_callback:
                    self.log_callback("RESPONSE_CLEANED", term, "PROCESADO", f"Respuesta procesada: {translation[:50]}...")
                
                # Eliminar duplicados y término original
                final_translation = self._remove_duplicates_and_original(translation, term)
                
                if final_translation:  # Solo devolver si hay traducción válida después del filtrado
                    return {
                        'translation': final_translation,
                        'context': context or 'Sin contexto específico',
                        'source_lang': source_lang,
                        'target_lang': target_lang
                    }
            else:
                # Log de error HTTP
                if self.log_callback:
                    self.log_callback("HTTP_ERROR", term, "ERROR", f"HTTP {response.status_code}: {response.text[:100]}...")
                    
            return None
            
        except Exception as e:
            print(f"Error translating '{term}': {str(e)}")
            return None
    
    async def translate_terms_batch(self, terms: List[Dict], source_lang: str, target_lang: str, 
                                  max_concurrent: int = None) -> Dict[str, dict]:
        """
        Traducir múltiples términos de forma asíncrona con optimizaciones
        
        Args:
            terms: Lista de diccionarios con términos a traducir
            source_lang: Idioma origen
            target_lang: Idioma destino
            max_concurrent: Máximo número de traducciones concurrentes (None = usar batch_size)
            
        Returns:
            Diccionario con término -> {translation, context, source_lang, target_lang}
        """
        translations = {}
        
        # Usar configuración por defecto si no se especifica
        if max_concurrent is None:
            max_concurrent = self.batch_size
        
        # Filtrar solo términos que necesitan traducción (Match parcial o No encontrado)
        terms_to_translate = [
            term for term in terms 
            if term.get('Tipo Match') in ['Parcial', 'No encontrado'] and 
               term.get('Término', '').strip()
        ]
        
        if not terms_to_translate:
            return translations
        
        # 1. Verificar caché para todos los términos primero
        cached_translations = {}
        remaining_terms = []
        
        for term_data in terms_to_translate:
            term = term_data['Término']
            
            # Usar traducción parcial TMX como contexto principal para Ollama
            context = term_data.get('TMX_Context', None)
            
            cached_result = self._get_from_cache(term, source_lang, target_lang, context)
            if cached_result:
                cached_translations[term] = cached_result
            else:
                remaining_terms.append(term_data)
        
        print(f"Cache hit: {len(cached_translations)}/{len(terms_to_translate)} términos")
        translations.update(cached_translations)
        
        if not remaining_terms:
            return translations
        
        # 2. Procesar términos restantes en lotes
        # Crear semáforo para limitar concurrencia
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def translate_single(term_data):
            async with semaphore:
                term = term_data['Término']
                # Usar traducción parcial TMX como contexto para Ollama
                context = term_data.get('TMX_Context', None)
                
                try:
                    # Usar requests en un executor para no bloquear
                    loop = asyncio.get_event_loop()
                    translation_result = await loop.run_in_executor(
                        None, 
                        self.translate_term, 
                        term, 
                        source_lang, 
                        target_lang,
                        context
                    )
                    
                    if translation_result:
                        return term, translation_result
                    return term, None
                    
                except Exception as e:
                    print(f"Error translating '{term}': {str(e)}")
                    return term, None
        
        # Ejecutar traducciones en paralelo solo para términos no cacheados
        tasks = [translate_single(term_data) for term_data in remaining_terms]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Procesar resultados
        for result in results:
            if isinstance(result, tuple) and len(result) == 2:
                term, translation_result = result
                if translation_result:
                    translations[term] = translation_result
        
        return translations
    
    def translate_batch_single_request(self, terms: List[str], source_lang: str, target_lang: str) -> Dict[str, str]:
        """
        Traducir múltiples términos en una sola petición (más eficiente para lotes grandes)
        
        Args:
            terms: Lista de términos a traducir
            source_lang: Idioma origen
            target_lang: Idioma destino
            
        Returns:
            Diccionario con término -> traducción
        """
        if not terms:
            return {}
        
        # Mapeo de códigos de idioma
        lang_names = {
            'es': 'Spanish', 'en': 'English', 'fr': 'French',
            'de': 'German', 'it': 'Italian', 'pt': 'Portuguese',
            'ca': 'Catalan', 'eu': 'Basque', 'gl': 'Galician'
        }
        
        source_name = lang_names.get(source_lang, source_lang)
        target_name = lang_names.get(target_lang, target_lang)
        
        # Crear prompt para múltiples términos
        terms_list = '\n'.join([f"{i+1}. {term}" for i, term in enumerate(terms)])
        
        prompt = f"""You are a professional technical translator. Translate the following terms from {source_name} to {target_name}.

Terms to translate:
{terms_list}

Instructions:
- Provide ALL possible accurate technical translations for each term
- If multiple valid translations exist, separate them with " | "
- Maintain the same numbering format in your response
- Include formal, informal, abbreviated, and alternative forms
- Order translations from most common to least common
- If a term is a proper noun or doesn't need translation, return it as is

Format your response exactly like this:
1. [translations for term 1]
2. [translations for term 2]
...

Translations:"""

        try:
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.1,
                    "top_p": 0.9,
                    "max_tokens": len(terms) * 50  # Más tokens para múltiples términos
                }
            }
            
            response = requests.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=self.timeout * 2  # Más tiempo para lotes
            )
            
            if response.status_code == 200:
                result = response.json()
                response_text = result.get('response', '').strip()
                
                # Parsear respuesta
                return self._parse_batch_response(response_text, terms)
            
        except Exception as e:
            print(f"Error in batch translation: {str(e)}")
        
        return {}
    
    def _parse_batch_response(self, response_text: str, original_terms: List[str]) -> Dict[str, str]:
        """Parsear respuesta de traducción por lotes"""
        translations = {}
        lines = response_text.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Buscar patrón "número. traducción"
            import re
            match = re.match(r'^(\d+)\.\s*(.+)$', line)
            if match:
                index = int(match.group(1)) - 1  # Convertir a índice 0-based
                translation = match.group(2).strip()
                
                if 0 <= index < len(original_terms):
                    original_term = original_terms[index]
                    cleaned_translation = self._clean_translation(translation)
                    if cleaned_translation and cleaned_translation.lower() != original_term.lower():
                        translations[original_term] = cleaned_translation
        
        return translations
    
    def clear_cache(self, source_lang: str = None, target_lang: str = None):
        """Limpiar caché de traducciones"""
        if source_lang and target_lang:
            # Limpiar caché específico
            cache_file = self._get_cache_file_path(source_lang, target_lang)
            if cache_file.exists():
                cache_file.unlink()
            
            # Limpiar caché en memoria
            keys_to_remove = [k for k in self.memory_cache.keys() 
                            if f"|{source_lang}|{target_lang}|" in k]
            for key in keys_to_remove:
                del self.memory_cache[key]
        else:
            # Limpiar todo el caché
            import shutil
            if self.cache_dir.exists():
                shutil.rmtree(self.cache_dir)
                self.cache_dir.mkdir(exist_ok=True)
            self.memory_cache.clear()
    
    def get_cache_stats(self) -> Dict[str, any]:
        """Obtener estadísticas del caché"""
        stats = {
            'memory_cache_size': len(self.memory_cache),
            'cache_files': [],
            'total_cached_translations': 0
        }
        
        if self.cache_dir.exists():
            for cache_file in self.cache_dir.glob("translations_*.json"):
                try:
                    with open(cache_file, 'r', encoding='utf-8') as f:
                        cache_data = json.load(f)
                        stats['cache_files'].append({
                            'file': cache_file.name,
                            'translations': len(cache_data),
                            'size_kb': cache_file.stat().st_size / 1024
                        })
                        stats['total_cached_translations'] += len(cache_data)
                except Exception:
                    pass
        
        return stats
    
    def _clean_translation(self, translation: str) -> str:
        """Limpiar la respuesta de traducción y manejar múltiples opciones"""
        if not translation:
            return ""
        
        # Remover comillas y espacios extra
        translation = translation.strip().strip('"').strip("'").strip()
        
        # Manejar caso NOT_FOUND
        if translation.upper() == "NOT_FOUND":
            return ""
        
        # NUEVO: Limpiar símbolos y caracteres extraños al inicio
        # Remover asteriscos, flechas y otros símbolos al inicio
        import re
        translation = re.sub(r'^[\*\→\→\-\>\<\[\]]+\s*', '', translation)
        
        # Remover comillas al inicio y final
        translation = re.sub(r'^["\'"]+|["\'"]+$', '', translation)
        
        # MEJORADO: Manejar respuestas largas de Ollama que incluyen explicaciones
        # Buscar patrones de respuestas explicativas y extraer solo la traducción
        
        # Patrón 1: "Based on the provided TMX context, I found the following translations for the term "X": Y"
        pattern1 = r'Based on.*?translations?.*?for.*?the term.*?["\']([^"\']+)["\'].*?:\s*(.+?)(?:\.|$)'
        match1 = re.search(pattern1, translation, re.IGNORECASE | re.DOTALL)
        if match1:
            translation = match1.group(2).strip()
        
        # Patrón 2: "Based on the provided TMX context, I found the following: Y"
        pattern2 = r'Based on.*?context.*?I found.*?following.*?:\s*(.+?)(?:\.|$)'
        match2 = re.search(pattern2, translation, re.IGNORECASE | re.DOTALL)
        if match2:
            translation = match2.group(1).strip()
        
        # Patrón 3: "Based on the TMX context provided, I found: Y"
        pattern3 = r'Based on.*?TMX.*?context.*?I found.*?:\s*(.+?)(?:\.|$)'
        match3 = re.search(pattern3, translation, re.IGNORECASE | re.DOTALL)
        if match3:
            translation = match3.group(1).strip()
        
        # Patrón 4: Cualquier texto que termine con ": traducción"
        pattern4 = r'.*?:\s*(.+?)(?:\.|$)'
        if any(phrase in translation.lower() for phrase in ['based on', 'context', 'found', 'following']):
            match4 = re.search(pattern4, translation, re.IGNORECASE | re.DOTALL)
            if match4:
                potential_translation = match4.group(1).strip()
                # Solo usar si parece una traducción válida (no muy larga)
                if len(potential_translation) < 200 and not any(phrase in potential_translation.lower() for phrase in ['based on', 'context', 'found']):
                    translation = potential_translation
        
        # Remover prefijos comunes de respuesta
        prefixes_to_remove = [
            "Translation:", "Traducción:", "The translation is:",
            "La traducción es:", "Answer:", "Respuesta:", "Translations:",
            "Based on", "According to", "I found", "The term", "Here is",
            "Here are", "The translations are", "The translation would be"
        ]
        
        for prefix in prefixes_to_remove:
            if translation.lower().startswith(prefix.lower()):
                # Buscar el primer ":" después del prefijo y tomar lo que sigue
                colon_pos = translation.find(':', len(prefix))
                if colon_pos != -1:
                    translation = translation[colon_pos + 1:].strip()
                else:
                    translation = translation[len(prefix):].strip()
        
        # NUEVO: Limpiar patrones específicos problemáticos
        # Remover patrones como "* término →" o "término →"
        translation = re.sub(r'^\*\s*[^→]+\s*→\s*', '', translation)
        translation = re.sub(r'^[^→]+\s*→\s*', '', translation)
        
        # Remover asteriscos sueltos al inicio
        translation = re.sub(r'^\*\s*', '', translation)
        
        # Limpiar patrones como '"término" → "traducción"' y quedarse solo con la traducción
        quote_arrow_pattern = r'^["\']?([^"\']+)["\']?\s*→\s*["\']?([^"\']+)["\']?$'
        quote_match = re.search(quote_arrow_pattern, translation)
        if quote_match:
            translation = quote_match.group(2).strip()
        
        # Tomar solo la primera línea si hay múltiples líneas
        translation = translation.split('\n')[0].strip()
        
        # Verificar de nuevo NOT_FOUND después de limpiar
        if translation.upper() == "NOT_FOUND":
            return ""
        
        # Remover texto explicativo adicional al final
        # Si contiene frases explicativas, cortarlas
        explanatory_phrases = [
            "based on", "according to", "in the context", "this is", "this term",
            "which means", "referring to", "in this case", "specifically"
        ]
        
        for phrase in explanatory_phrases:
            if phrase in translation.lower():
                # Tomar solo la parte antes de la explicación
                parts = translation.lower().split(phrase)
                if len(parts) > 1:
                    translation = parts[0].strip()
                    break
        
        # Limpiar y validar múltiples traducciones separadas por |
        if '|' in translation:
            # Dividir por | y limpiar cada parte
            parts = [part.strip() for part in translation.split('|')]
            # Filtrar partes vacías, NOT_FOUND y muy largas
            valid_parts = []
            for part in parts:
                # Limpiar cada parte individualmente
                part = re.sub(r'^\*\s*', '', part)  # Remover asteriscos
                part = re.sub(r'^["\'"]+|["\'"]+$', '', part)  # Remover comillas
                part = part.strip()
                
                if (part and len(part) > 1 and len(part) < 100 and 
                    part.upper() != "NOT_FOUND" and
                    not any(phrase in part.lower() for phrase in ['based on', 'context', 'found'])):
                    valid_parts.append(part)
            
            if valid_parts:
                translation = ' | '.join(valid_parts)
            else:
                return ""
        
        # Limpiar caracteres extraños finales
        translation = re.sub(r'^\*\s*', '', translation)  # Asteriscos al inicio
        translation = re.sub(r'^["\'"]+|["\'"]+$', '', translation)  # Comillas
        translation = translation.rstrip('.,;:')  # Puntuación al final
        
        # Verificación final: si la traducción es muy larga o contiene texto explicativo, descartarla
        if (len(translation) > 200 or 
            any(phrase in translation.lower() for phrase in ['based on', 'according to', 'i found', 'context provided'])):
            return ""
        
        return translation.strip()
    
    def _remove_duplicates_and_original(self, translation: str, original_term: str) -> str:
        """Eliminar duplicados y el término original de la traducción"""
        if not translation:
            return ""
        
        # Dividir por | si existe
        if '|' in translation:
            parts = [part.strip() for part in translation.split('|')]
        else:
            parts = [translation.strip()]
        
        # Normalizar para comparación (minúsculas)
        original_lower = original_term.lower()
        
        # Filtrar duplicados y término original
        seen = set()
        filtered_parts = []
        
        for part in parts:
            part_lower = part.lower()
            # Saltar si es el término original o ya lo hemos visto
            if part_lower != original_lower and part_lower not in seen:
                seen.add(part_lower)
                filtered_parts.append(part)
        
        # Unir las partes filtradas
        if filtered_parts:
            return ' | '.join(filtered_parts)
        else:
            return ""
    
    def classify_domain_relevance(self, term: str, domain_description: str, language: str = "es") -> Optional[dict]:
        """
        Clasificar si un término es relevante para el ámbito/dominio descrito por el usuario
        
        Args:
            term: Término a clasificar
            domain_description: Descripción del ámbito/dominio del usuario
            language: Idioma del término (por defecto español)
            
        Returns:
            Diccionario con relevancia y puntuación, o None si falla
        """
        # Log inicio
        if self.log_callback:
            self.log_callback("DOMAIN_CLASSIFY_START", term, "INICIANDO", f"Clasificando relevancia para ámbito: {domain_description[:50]}...")
        
        # Verificar caché primero
        cache_key = self._get_cache_key(term, language, "domain_classification", domain_description)
        if cache_key in self.memory_cache:
            if self.log_callback:
                self.log_callback("DOMAIN_CACHE_HIT", term, "CACHE", "Clasificación encontrada en caché")
            return self.memory_cache[cache_key]
        
        # Si no está en caché, clasificar con reintentos
        if self.log_callback:
            self.log_callback("DOMAIN_CACHE_MISS", term, "CLASIFICANDO", "No encontrado en caché, consultando Ollama...")
        
        for attempt in range(self.max_retries + 1):
            try:
                if self.log_callback and attempt > 0:
                    self.log_callback("DOMAIN_RETRY", term, "REINTENTANDO", f"Intento {attempt + 1}/{self.max_retries + 1}")
                
                result = self._classify_with_ollama(term, domain_description, language)
                if result:
                    # Guardar en caché
                    self.memory_cache[cache_key] = result
                    if self.log_callback:
                        self.log_callback("DOMAIN_CLASSIFY_SUCCESS", term, "COMPLETADO", f"Relevancia: {result['relevance']} ({result['confidence']}%)")
                    return result
            except Exception as e:
                error_msg = str(e)
                if self.log_callback:
                    self.log_callback("DOMAIN_CLASSIFY_ERROR", term, "ERROR", f"Intento {attempt + 1} falló: {error_msg[:50]}...")
                print(f"Domain classification attempt {attempt + 1} failed for '{term}': {error_msg}")
                if attempt < self.max_retries:
                    import time
                    time.sleep(1)
        
        if self.log_callback:
            self.log_callback("DOMAIN_CLASSIFY_FAILED", term, "FALLIDO", f"Falló después de {self.max_retries + 1} intentos")
        return None
    
    def _classify_with_ollama(self, term: str, domain_description: str, language: str) -> Optional[dict]:
        """Realizar la clasificación real con Ollama"""
        try:
            # Mapeo de códigos de idioma a nombres completos
            lang_names = {
                'es': 'Spanish',
                'en': 'English', 
                'fr': 'French',
                'de': 'German',
                'it': 'Italian',
                'pt': 'Portuguese',
                'ca': 'Catalan',
                'eu': 'Basque',
                'gl': 'Galician'
            }
            
            lang_name = lang_names.get(language, language)
            
            # Crear prompt para clasificación de relevancia al ámbito
            prompt = f"""You are an expert domain classifier. Analyze if the given term is relevant to the specified domain/scope.

Term to analyze: "{term}"
Language: {lang_name}
Domain/Scope: "{domain_description}"

Instructions:
- Determine if the term is directly related to the specified domain
- Consider technical terminology, concepts, processes, tools, or entities specific to that domain
- Provide a relevance classification: "Sí" (Yes), "No", or "Incierto" (Uncertain)
- Provide a confidence percentage (0-100)
- Be strict: only classify as "Sí" if the term is clearly and specifically related to the domain
- Generic terms that could apply to any domain should be classified as "No" or "Incierto"

Examples:
- Term: "cardiovascular" Domain: "medicina" → Sí (95%)
- Term: "usuario" Domain: "medicina" → No (10%)
- Term: "sistema" Domain: "ingeniería de software" → Incierto (40%)
- Term: "algoritmo" Domain: "ingeniería de software" → Sí (90%)

Respond in this exact format:
Relevance: [Sí/No/Incierto]
Confidence: [0-100]%
Reason: [Brief explanation in {lang_name}]"""
            
            # Log del prompt enviado
            if self.log_callback:
                self.log_callback("DOMAIN_PROMPT_SENT", term, "ENVIANDO", f"Enviando prompt de clasificación...", prompt=prompt)
            
            # Hacer petición a Ollama
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.1,  # Baja temperatura para clasificaciones más consistentes
                    "top_p": 0.9,
                    "max_tokens": 100
                }
            }
            
            response = requests.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                raw_response = result.get('response', '').strip()
                
                # Log de la respuesta cruda
                if self.log_callback:
                    self.log_callback("DOMAIN_RESPONSE_RECEIVED", term, "RESPUESTA", f"Respuesta cruda recibida", response=raw_response)
                
                # Parsear la respuesta
                classification = self._parse_domain_classification(raw_response)
                
                if classification:
                    # Log de la respuesta procesada
                    if self.log_callback:
                        self.log_callback("DOMAIN_RESPONSE_PARSED", term, "PROCESADO", f"Clasificación: {classification['relevance']} ({classification['confidence']}%)")
                    
                    return {
                        'relevance': classification['relevance'],
                        'confidence': classification['confidence'],
                        'reason': classification.get('reason', ''),
                        'domain': domain_description,
                        'language': language
                    }
            else:
                # Log de error HTTP
                if self.log_callback:
                    self.log_callback("DOMAIN_HTTP_ERROR", term, "ERROR", f"HTTP {response.status_code}: {response.text[:100]}...")
                    
            return None
            
        except Exception as e:
            print(f"Error classifying domain relevance for '{term}': {str(e)}")
            return None
    
    def _parse_domain_classification(self, response_text: str) -> Optional[dict]:
        """Parsear respuesta de clasificación de dominio"""
        try:
            lines = response_text.split('\n')
            classification = {}
            
            for line in lines:
                line = line.strip()
                if line.lower().startswith('relevance:') or line.lower().startswith('relevancia:'):
                    # Extraer relevancia
                    relevance_part = line.split(':', 1)[1].strip()
                    if 'sí' in relevance_part.lower() or 'yes' in relevance_part.lower():
                        classification['relevance'] = 'Sí'
                    elif 'no' in relevance_part.lower():
                        classification['relevance'] = 'No'
                    elif 'incierto' in relevance_part.lower() or 'uncertain' in relevance_part.lower():
                        classification['relevance'] = 'Incierto'
                
                elif line.lower().startswith('confidence:') or line.lower().startswith('confianza:'):
                    # Extraer confianza
                    confidence_part = line.split(':', 1)[1].strip()
                    import re
                    confidence_match = re.search(r'(\d+)', confidence_part)
                    if confidence_match:
                        classification['confidence'] = int(confidence_match.group(1))
                
                elif line.lower().startswith('reason:') or line.lower().startswith('razón:'):
                    # Extraer razón
                    reason_part = line.split(':', 1)[1].strip()
                    classification['reason'] = reason_part
            
            # Validar que tenemos los campos mínimos
            if 'relevance' in classification and 'confidence' in classification:
                # Asegurar valores por defecto
                if 'reason' not in classification:
                    classification['reason'] = 'Sin explicación'
                
                # Validar rango de confianza
                classification['confidence'] = max(0, min(100, classification['confidence']))
                
                return classification
            
            return None
            
        except Exception as e:
            print(f"Error parsing domain classification: {str(e)}")
            return None
    
    async def classify_terms_domain_batch(self, terms: List[str], domain_description: str, 
                                        language: str = "es", max_concurrent: int = None) -> Dict[str, dict]:
        """
        Clasificar múltiples términos por relevancia al dominio de forma asíncrona
        
        Args:
            terms: Lista de términos a clasificar
            domain_description: Descripción del ámbito/dominio
            language: Idioma de los términos
            max_concurrent: Máximo número de clasificaciones concurrentes
            
        Returns:
            Diccionario con término -> {relevance, confidence, reason, domain, language}
        """
        classifications = {}
        
        # Usar configuración por defecto si no se especifica
        if max_concurrent is None:
            max_concurrent = self.batch_size
        
        if not terms or not domain_description.strip():
            return classifications
        
        # 1. Verificar caché para todos los términos primero
        cached_classifications = {}
        remaining_terms = []
        
        for term in terms:
            cache_key = self._get_cache_key(term, language, "domain_classification", domain_description)
            if cache_key in self.memory_cache:
                cached_classifications[term] = self.memory_cache[cache_key]
            else:
                remaining_terms.append(term)
        
        print(f"Domain classification cache hit: {len(cached_classifications)}/{len(terms)} términos")
        classifications.update(cached_classifications)
        
        if not remaining_terms:
            return classifications
        
        # 2. Procesar términos restantes en lotes
        # Crear semáforo para limitar concurrencia
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def classify_single(term):
            async with semaphore:
                try:
                    # Usar requests en un executor para no bloquear
                    loop = asyncio.get_event_loop()
                    classification_result = await loop.run_in_executor(
                        None, 
                        self.classify_domain_relevance, 
                        term, 
                        domain_description,
                        language
                    )
                    
                    if classification_result:
                        return term, classification_result
                    return term, None
                    
                except Exception as e:
                    print(f"Error classifying domain relevance for '{term}': {str(e)}")
                    return term, None
        
        # Ejecutar clasificaciones en paralelo solo para términos no cacheados
        tasks = [classify_single(term) for term in remaining_terms]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Procesar resultados
        for result in results:
            if isinstance(result, tuple) and len(result) == 2:
                term, classification_result = result
                if classification_result:
                    classifications[term] = classification_result
        
        return classifications

    async def translate_and_classify_unified_batch(
        self, 
        terms_data: List[Dict], 
        source_lang: str, 
        target_lang: str,
        domain_description: str,
        max_concurrent: int = None
    ) -> Dict[str, dict]:
        """
        MÉTODO UNIFICADO: Traducir Y clasificar términos en una sola llamada por término
        
        Args:
            terms_data: Lista de diccionarios con términos a procesar
            source_lang: Idioma origen
            target_lang: Idioma destino  
            domain_description: Descripción del ámbito/dominio
            max_concurrent: Máximo número de llamadas concurrentes
            
        Returns:
            Diccionario con término -> {translation, domain_relevance, confidence, reason, ...}
        """
        unified_results = {}
        
        # Usar configuración optimizada
        if max_concurrent is None:
            max_concurrent = int(os.getenv('OLLAMA_MAX_CONCURRENT', '10'))  # Aumentado de 3 a 10
        
        # Filtrar términos que necesitan procesamiento
        terms_to_process = [
            term for term in terms_data 
            if term.get('Tipo Match') in ['Parcial', 'No encontrado'] and 
               term.get('Término', '').strip()
        ]
        
        if not terms_to_process:
            return unified_results
        
        # 1. Verificar caché unificado primero
        cached_results = {}
        remaining_terms = []
        
        for term_data in terms_to_process:
            term = term_data['Término']
            context = term_data.get('TMX_Context', '')
            
            # Clave de caché unificada
            cache_key = self._get_unified_cache_key(term, source_lang, target_lang, context, domain_description)
            
            if cache_key in self.memory_cache:
                cached_results[term] = self.memory_cache[cache_key]
            else:
                remaining_terms.append(term_data)
        
        print(f"Unified cache hit: {len(cached_results)}/{len(terms_to_process)} términos")
        unified_results.update(cached_results)
        
        if not remaining_terms:
            return unified_results
        
        # 2. Procesar términos restantes con llamadas unificadas
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def process_unified_single(term_data):
            async with semaphore:
                term = term_data['Término']
                context = term_data.get('TMX_Context', '')
                
                try:
                    # Usar requests en un executor para no bloquear
                    loop = asyncio.get_event_loop()
                    unified_result = await loop.run_in_executor(
                        None, 
                        self._translate_and_classify_unified_single, 
                        term, 
                        source_lang, 
                        target_lang,
                        context,
                        domain_description
                    )
                    
                    if unified_result:
                        # Guardar en caché unificado
                        cache_key = self._get_unified_cache_key(term, source_lang, target_lang, context, domain_description)
                        self.memory_cache[cache_key] = unified_result
                        return term, unified_result
                    return term, None
                    
                except Exception as e:
                    print(f"Error in unified processing for '{term}': {str(e)}")
                    return term, None
        
        # Ejecutar procesamiento unificado en paralelo
        tasks = [process_unified_single(term_data) for term_data in remaining_terms]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Procesar resultados
        for result in results:
            if isinstance(result, tuple) and len(result) == 2:
                term, unified_result = result
                if unified_result:
                    unified_results[term] = unified_result
        
        return unified_results

    def _get_unified_cache_key(self, term: str, source_lang: str, target_lang: str, context: str, domain_description: str) -> str:
        """Generar clave única para caché unificado"""
        import hashlib
        key_data = f"UNIFIED|{term}|{source_lang}|{target_lang}|{context or ''}|{domain_description or ''}"
        return hashlib.md5(key_data.encode()).hexdigest()

    def _translate_and_classify_unified_single(
        self, 
        term: str, 
        source_lang: str, 
        target_lang: str, 
        context: str, 
        domain_description: str
    ) -> Optional[dict]:
        """
        Procesar UN término con traducción + clasificación en una sola llamada
        """
        try:
            # Log inicio
            if self.log_callback:
                self.log_callback("UNIFIED_START", term, "INICIANDO", f"Traducción + Clasificación unificada")
            
            # Crear prompt unificado
            prompt = self._create_unified_prompt(term, source_lang, target_lang, context, domain_description)
            
            # Log del prompt
            if self.log_callback:
                self.log_callback("UNIFIED_PROMPT_SENT", term, "ENVIANDO", f"Prompt unificado enviado", prompt=prompt)
            
            # Hacer petición a Ollama
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.1,
                    "top_p": 0.9,
                    "max_tokens": 150  # Más tokens para respuesta JSON
                }
            }
            
            response = requests.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=int(os.getenv('OLLAMA_TIMEOUT', '45'))  # Timeout aumentado
            )
            
            if response.status_code == 200:
                result = response.json()
                raw_response = result.get('response', '').strip()
                
                # Log respuesta cruda
                if self.log_callback:
                    self.log_callback("UNIFIED_RESPONSE_RECEIVED", term, "RESPUESTA", f"Respuesta unificada recibida", response=raw_response)
                
                # Parsear respuesta JSON unificada
                unified_data = self._parse_unified_response(raw_response)
                
                if unified_data:
                    # Log éxito
                    if self.log_callback:
                        translation = unified_data.get('translation', '')
                        relevance = unified_data.get('domain_relevance', '')
                        confidence = unified_data.get('confidence', 0)
                        self.log_callback("UNIFIED_SUCCESS", term, "COMPLETADO", f"Trad: '{translation}' | Dom: {relevance} ({confidence}%)")
                    
                    return {
                        'translation': unified_data.get('translation', ''),
                        'context': context or 'Sin contexto específico',
                        'source_lang': source_lang,
                        'target_lang': target_lang,
                        'domain_relevance': unified_data.get('domain_relevance', 'Error'),
                        'confidence': unified_data.get('confidence', 0),
                        'reason': unified_data.get('reason', 'Sin razón'),
                        'domain_description': domain_description
                    }
            else:
                # Log error HTTP
                if self.log_callback:
                    self.log_callback("UNIFIED_HTTP_ERROR", term, "ERROR", f"HTTP {response.status_code}")
            
            return None
            
        except Exception as e:
            if self.log_callback:
                self.log_callback("UNIFIED_ERROR", term, "ERROR", f"Error: {str(e)[:100]}")
            print(f"Error in unified processing for '{term}': {str(e)}")
            return None

    def _create_unified_prompt(self, term: str, source_lang: str, target_lang: str, context: str, domain_description: str) -> str:
        """
        Crear prompt unificado que hace traducción + clasificación en una sola llamada
        """
        # Mapeo de idiomas
        lang_names = {
            'es': 'Spanish', 'en': 'English', 'fr': 'French',
            'de': 'German', 'it': 'Italian', 'pt': 'Portuguese',
            'ca': 'Catalan', 'eu': 'Basque', 'gl': 'Galician'
        }
        
        source_name = lang_names.get(source_lang, source_lang)
        target_name = lang_names.get(target_lang, target_lang)
        
        # Prompt unificado optimizado
        prompt = f"""You are a technical translator and domain classifier. Process the term "{term}" from {source_name} to {target_name}.

TASKS:
1. TRANSLATE: Based on TMX context: "{context}"
2. CLASSIFY: Relevance to domain: "{domain_description}"

TMX TRANSLATION RULES:
- Extract ONLY translations that appear in the TMX context
- If no translation in context, provide best technical translation
- Clean output, no explanations or symbols

DOMAIN CLASSIFICATION RULES:  
- "Sí": Term is directly related to the domain
- "No": Term is generic or unrelated to domain
- "Incierto": Uncertain relevance
- Be strict: only "Sí" for clearly domain-specific terms

RESPOND in this EXACT JSON format (no other text):
{{
    "translation": "clean translation here",
    "domain_relevance": "Sí",
    "confidence": 85,
    "reason": "brief explanation in {source_name}"
}}"""

        return prompt

    def _parse_unified_response(self, response_text: str) -> Optional[dict]:
        """
        Parsear respuesta JSON unificada de Ollama
        """
        try:
            # Limpiar respuesta para extraer JSON
            response_text = response_text.strip()
            
            # Buscar JSON en la respuesta
            import re
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                json_text = json_match.group(0)
                
                # Intentar parsear JSON
                import json
                data = json.loads(json_text)
                
                # Validar campos requeridos
                if all(key in data for key in ['translation', 'domain_relevance', 'confidence']):
                    # Limpiar traducción
                    data['translation'] = self._clean_translation(data['translation'])
                    
                    # Validar relevancia
                    if data['domain_relevance'] not in ['Sí', 'No', 'Incierto']:
                        data['domain_relevance'] = 'Error'
                    
                    # Validar confianza
                    try:
                        data['confidence'] = max(0, min(100, int(data['confidence'])))
                    except:
                        data['confidence'] = 0
                    
                    # Asegurar razón
                    if 'reason' not in data:
                        data['reason'] = 'Sin explicación'
                    
                    return data
            
            return None
            
        except Exception as e:
            print(f"Error parsing unified response: {str(e)}")
            return None

    def test_connection(self) -> Dict[str, any]:
        """Probar conexión con Ollama y obtener información"""
        try:
            # Verificar disponibilidad
            available = self.is_available()
            
            if not available:
                return {
                    'available': False,
                    'error': f'No se puede conectar a Ollama en {self.base_url}'
                }
            
            # Obtener modelos disponibles
            models = self.get_available_models()
            
            # Probar traducción simple con múltiples opciones
            test_result = self.translate_term("management system", "en", "es")
            test_translation = test_result['translation'] if test_result else None
            
            # Probar clasificación de dominio
            test_domain_result = self.classify_domain_relevance("algoritmo", "ingeniería de software", "es")
            test_domain_classification = f"{test_domain_result['relevance']} ({test_domain_result['confidence']}%)" if test_domain_result else None
            
            return {
                'available': True,
                'host': self.ollama_host,
                'port': self.ollama_port,
                'url': self.base_url,
                'model': self.model,
                'available_models': models,
                'test_translation': test_translation,
                'test_domain_classification': test_domain_classification
            }
            
        except Exception as e:
            return {
                'available': False,
                'error': str(e)
            }