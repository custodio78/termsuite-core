from lxml import etree
from typing import List, Dict
from pathlib import Path


class TMXParser:
    """Parser para archivos TMX (Translation Memory eXchange)"""
    
    def parse(self, tmx_path: str) -> List[str]:
        """
        Parsear archivo TMX y extraer términos únicos
        
        Args:
            tmx_path: Ruta al archivo TMX
            
        Returns:
            Lista de términos únicos
        """
        terms = set()
        
        try:
            tree = etree.parse(tmx_path)
            root = tree.getroot()
            
            # Namespace TMX
            ns = {'tmx': 'http://www.lisa.org/tmx14'}
            
            # Extraer todos los segmentos de texto
            for tu in root.findall('.//tmx:tu', ns):
                for tuv in tu.findall('.//tmx:tuv', ns):
                    seg = tuv.find('.//tmx:seg', ns)
                    if seg is not None and seg.text:
                        # Limpiar y agregar término
                        term = seg.text.strip()
                        if term:
                            terms.add(term)
            
            # Si no hay namespace, intentar sin él
            if not terms:
                for seg in root.findall('.//seg'):
                    if seg.text:
                        term = seg.text.strip()
                        if term:
                            terms.add(term)
        
        except Exception as e:
            raise Exception(f"Error al parsear TMX: {str(e)}")
        
        return sorted(list(terms))
    
    def parse_with_translations(self, tmx_path: str) -> List[Dict[str, str]]:
        """
        Parsear TMX y extraer pares de traducción
        
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
                    source_seg = tuvs[0].find('.//tmx:seg', ns)
                    target_seg = tuvs[1].find('.//tmx:seg', ns)
                    
                    if source_seg is not None and target_seg is not None:
                        translations.append({
                            'source': source_seg.text.strip() if source_seg.text else '',
                            'target': target_seg.text.strip() if target_seg.text else ''
                        })
        
        except Exception as e:
            raise Exception(f"Error al parsear TMX: {str(e)}")
        
        return translations
