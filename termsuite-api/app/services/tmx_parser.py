from lxml import etree
from typing import List, Dict
from pathlib import Path
from collections import Counter


class TMXParser:
    """Parser para archivos TMX (Translation Memory eXchange)"""
    
    def parse(self, tmx_path: str, language: str = None) -> List[str]:
        """
        Parsear archivo TMX y extraer términos únicos de un idioma específico
        
        Args:
            tmx_path: Ruta al archivo TMX
            language: Código de idioma (en, es, fr, de, etc.). Si es None, extrae todos.
            
        Returns:
            Lista de términos únicos del idioma especificado
        """
        terms = set()
        
        try:
            tree = etree.parse(tmx_path)
            root = tree.getroot()
            
            # Namespace TMX
            ns = {'tmx': 'http://www.lisa.org/tmx14'}
            
            # Extraer segmentos de texto del idioma especificado
            for tu in root.findall('.//tmx:tu', ns):
                for tuv in tu.findall('.//tmx:tuv', ns):
                    # Obtener el idioma del segmento
                    lang_attr = tuv.get('{http://www.w3.org/XML/1998/namespace}lang')
                    if not lang_attr:
                        lang_attr = tuv.get('lang')
                    
                    # Si se especificó idioma, filtrar
                    if language:
                        if lang_attr and not self._match_language(lang_attr, language):
                            continue
                    
                    seg = tuv.find('.//tmx:seg', ns)
                    if seg is not None and seg.text:
                        term = seg.text.strip()
                        if term:
                            terms.add(term)
            
            # Si no hay namespace, intentar sin él
            if not terms:
                for tuv in root.findall('.//tuv'):
                    lang_attr = tuv.get('{http://www.w3.org/XML/1998/namespace}lang')
                    if not lang_attr:
                        lang_attr = tuv.get('lang')
                    
                    if language:
                        if lang_attr and not self._match_language(lang_attr, language):
                            continue
                    
                    seg = tuv.find('.//seg')
                    if seg is not None and seg.text:
                        term = seg.text.strip()
                        if term:
                            terms.add(term)
        
        except Exception as e:
            raise Exception(f"Error al parsear TMX: {str(e)}")
        
        return sorted(list(terms))
    
    def parse_with_frequency(self, tmx_path: str, language: str = None) -> Dict[str, int]:
        """
        Parsear archivo TMX y contar frecuencia de términos
        
        Args:
            tmx_path: Ruta al archivo TMX
            language: Código de idioma (en, es, fr, de, etc.). Si es None, extrae todos.
            
        Returns:
            Diccionario con términos y su frecuencia
        """
        from collections import Counter
        terms = []
        
        try:
            tree = etree.parse(tmx_path)
            root = tree.getroot()
            
            # Namespace TMX
            ns = {'tmx': 'http://www.lisa.org/tmx14'}
            
            # Extraer segmentos de texto del idioma especificado
            for tu in root.findall('.//tmx:tu', ns):
                for tuv in tu.findall('.//tmx:tuv', ns):
                    # Obtener el idioma del segmento
                    lang_attr = tuv.get('{http://www.w3.org/XML/1998/namespace}lang')
                    if not lang_attr:
                        lang_attr = tuv.get('lang')
                    
                    # Si se especificó idioma, filtrar
                    if language:
                        if lang_attr and not self._match_language(lang_attr, language):
                            continue
                    
                    seg = tuv.find('.//tmx:seg', ns)
                    if seg is not None and seg.text:
                        term = seg.text.strip()
                        if term:
                            terms.add(term)
            
            # Si no hay namespace, intentar sin él
            if not terms:
                for tuv in root.findall('.//tuv'):
                    lang_attr = tuv.get('{http://www.w3.org/XML/1998/namespace}lang')
                    if not lang_attr:
                        lang_attr = tuv.get('lang')
                    
                    if language:
                        if lang_attr and not self._match_language(lang_attr, language):
                            continue
                    
                    seg = tuv.find('.//seg')
                    if seg is not None and seg.text:
                        term = seg.text.strip()
                        if term:
                            terms.add(term)
        
        except Exception as e:
            raise Exception(f"Error al parsear TMX: {str(e)}")
        
        return sorted(list(terms))
    
    def parse_with_frequency(self, tmx_path: str, language: str = None) -> Dict[str, int]:
        """
        Parsear archivo TMX y contar frecuencia de términos
        
        Args:
            tmx_path: Ruta al archivo TMX
            language: Código de idioma (en, es, fr, de, etc.). Si es None, extrae todos.
            
        Returns:
            Diccionario con términos y su frecuencia
        """
        from collections import Counter
        terms = []
        
        try:
            tree = etree.parse(tmx_path)
            root = tree.getroot()
            
            # Namespace TMX
            ns = {'tmx': 'http://www.lisa.org/tmx14'}
            
            # Extraer todos los segmentos (con repeticiones)
            for tu in root.findall('.//tmx:tu', ns):
                for tuv in tu.findall('.//tmx:tuv', ns):
                    lang_attr = tuv.get('{http://www.w3.org/XML/1998/namespace}lang')
                    if not lang_attr:
                        lang_attr = tuv.get('lang')
                    
                    if language:
                        if lang_attr and not self._match_language(lang_attr, language):
                            continue
                    
                    seg = tuv.find('.//tmx:seg', ns)
                    if seg is not None and seg.text:
                        term = seg.text.strip()
                        if term:
                            terms.append(term)
            
            # Si no hay namespace, intentar sin él
            if not terms:
                for tuv in root.findall('.//tuv'):
                    lang_attr = tuv.get('{http://www.w3.org/XML/1998/namespace}lang')
                    if not lang_attr:
                        lang_attr = tuv.get('lang')
                    
                    if language:
                        if lang_attr and not self._match_language(lang_attr, language):
                            continue
                    
                    seg = tuv.find('.//seg')
                    if seg is not None and seg.text:
                        term = seg.text.strip()
                        if term:
                            terms.append(term)
        
        except Exception as e:
            raise Exception(f"Error al parsear TMX: {str(e)}")
        
        # Contar frecuencias
        return dict(Counter(terms))
    
    def parse_with_translations(self, tmx_path: str, source_lang: str = None) -> List[Dict[str, str]]:
        """
        Parsear TMX y extraer pares de traducción
        
        Args:
            tmx_path: Ruta al archivo TMX
            source_lang: Idioma origen (ej: 'es'). Si es None, usa el primer <tuv>
            
        Returns:
            Lista de diccionarios con source y target
        """
        translations = []
        
        try:
            tree = etree.parse(tmx_path)
            root = tree.getroot()
            
            ns = {'tmx': 'http://www.lisa.org/tmx14'}
            
            for tu in root.findall('.//tmx:tu', ns):
                tuvs = tu.findall('.//tmx:tuv', ns)
                if len(tuvs) >= 2:
                    # Si se especifica idioma origen, buscar el <tuv> correcto
                    if source_lang:
                        source_tuv = None
                        target_tuv = None
                        
                        for tuv in tuvs:
                            lang_attr = tuv.get('{http://www.w3.org/XML/1998/namespace}lang')
                            if not lang_attr:
                                lang_attr = tuv.get('lang')
                            
                            if lang_attr and self._match_language(lang_attr, source_lang):
                                source_tuv = tuv
                            elif lang_attr and not self._match_language(lang_attr, source_lang):
                                target_tuv = tuv
                        
                        if source_tuv is not None and target_tuv is not None:
                            source_seg = source_tuv.find('.//tmx:seg', ns)
                            target_seg = target_tuv.find('.//tmx:seg', ns)
                            
                            if source_seg is not None and target_seg is not None:
                                translations.append({
                                    'source': source_seg.text.strip() if source_seg.text else '',
                                    'target': target_seg.text.strip() if target_seg.text else ''
                                })
                    else:
                        # Sin idioma especificado, usar primer y segundo <tuv>
                        source_seg = tuvs[0].find('.//tmx:seg', ns)
                        target_seg = tuvs[1].find('.//tmx:seg', ns)
                        
                        if source_seg is not None and target_seg is not None:
                            translations.append({
                                'source': source_seg.text.strip() if source_seg.text else '',
                                'target': target_seg.text.strip() if target_seg.text else ''
                            })
            
            # Si no hay namespace, intentar sin él
            if not translations:
                for tu in root.findall('.//tu'):
                    tuvs = tu.findall('.//tuv')
                    if len(tuvs) >= 2:
                        if source_lang:
                            source_tuv = None
                            target_tuv = None
                            
                            for tuv in tuvs:
                                lang_attr = tuv.get('{http://www.w3.org/XML/1998/namespace}lang')
                                if not lang_attr:
                                    lang_attr = tuv.get('lang')
                                
                                if lang_attr and self._match_language(lang_attr, source_lang):
                                    source_tuv = tuv
                                elif lang_attr:
                                    target_tuv = tuv
                            
                            if source_tuv is not None and target_tuv is not None:
                                source_seg = source_tuv.find('.//seg')
                                target_seg = target_tuv.find('.//seg')
                                
                                if source_seg is not None and target_seg is not None:
                                    translations.append({
                                        'source': source_seg.text.strip() if source_seg.text else '',
                                        'target': target_seg.text.strip() if target_seg.text else ''
                                    })
                        else:
                            source_seg = tuvs[0].find('.//seg')
                            target_seg = tuvs[1].find('.//seg')
                            
                            if source_seg is not None and target_seg is not None:
                                translations.append({
                                    'source': source_seg.text.strip() if source_seg.text else '',
                                    'target': target_seg.text.strip() if target_seg.text else ''
                                })
        
        except Exception as e:
            raise Exception(f"Error al parsear TMX: {str(e)}")
        
        return translations
    
    def get_available_languages(self, tmx_path: str) -> List[str]:
        """
        Obtener lista de idiomas disponibles en el TMX
        
        Args:
            tmx_path: Ruta al archivo TMX
            
        Returns:
            Lista de códigos de idioma únicos
        """
        languages = set()
        
        try:
            tree = etree.parse(tmx_path)
            root = tree.getroot()
            
            ns = {'tmx': 'http://www.lisa.org/tmx14'}
            
            # Buscar todos los atributos de idioma
            for tuv in root.findall('.//tmx:tuv', ns):
                lang_attr = tuv.get('{http://www.w3.org/XML/1998/namespace}lang')
                if not lang_attr:
                    lang_attr = tuv.get('lang')
                
                if lang_attr:
                    # Extraer código base (antes del guión)
                    lang_code = lang_attr.split('-')[0].lower()
                    languages.add(lang_code)
            
            # Si no hay namespace, intentar sin él
            if not languages:
                for tuv in root.findall('.//tuv'):
                    lang_attr = tuv.get('{http://www.w3.org/XML/1998/namespace}lang')
                    if not lang_attr:
                        lang_attr = tuv.get('lang')
                    
                    if lang_attr:
                        lang_code = lang_attr.split('-')[0].lower()
                        languages.add(lang_code)
        
        except Exception as e:
            raise Exception(f"Error al obtener idiomas del TMX: {str(e)}")
        
        return sorted(list(languages))
    
    def _match_language(self, lang_attr: str, target_lang: str) -> bool:
        """
        Comparar códigos de idioma (maneja variantes como en-US, en-GB, etc.)
        
        Args:
            lang_attr: Atributo de idioma del TMX (ej: "en-US", "es-ES")
            target_lang: Idioma objetivo (ej: "en", "es")
            
        Returns:
            True si coinciden
        """
        if not lang_attr:
            return False
        
        # Normalizar a minúsculas
        lang_attr = lang_attr.lower()
        target_lang = target_lang.lower()
        
        # Comparación exacta
        if lang_attr == target_lang:
            return True
        
        # Comparar solo el código base (antes del guión)
        lang_base = lang_attr.split('-')[0]
        return lang_base == target_lang
