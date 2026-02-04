"""
Utilidades para normalizar la columna Traducción en exportaciones.
"""

# Longitud máxima razonable para una celda de traducción en Excel
MAX_TRANSLATION_LENGTH = 180


def trim_translation_for_excel(value: str, max_length: int = MAX_TRANSLATION_LENGTH) -> str:
    """
    Ajusta la traducción para Excel: quita solo partes que parecen instrucciones
    (no traducciones) y limita la longitud total sin eliminar opciones válidas.
    """
    if not value or not isinstance(value, str):
        return value
    value = value.strip()
    if not value:
        return value
    # Partes que parecen instrucciones (no traducciones de término)
    instruction_starts = ("pry ", "insert ", "with a ", "with the ", "remove ", "open the ", "place the ")
    if " | " in value:
        parts = [p.strip() for p in value.split(" | ") if p.strip()]
        # Quitar solo las que claramente son instrucciones
        kept = [p for p in parts if not p.lower().startswith(instruction_starts)]
        if not kept:
            kept = [parts[0]]
        value = " | ".join(kept)
    if len(value) > max_length:
        value = value[: max_length - 3].rstrip() + "..."
    return value


def normalize_translation_options(value: str) -> str:
    """
    Normaliza la columna Traducción cuando hay varias opciones separadas por " | ".

    Reglas:
    - Si las opciones son distintas: mantener todas.
    - Si son iguales salvo mayúsculas/minúsculas: mantener solo la primera.
    """
    if not value or not isinstance(value, str):
        return value
    value = value.strip()
    if not value:
        return value
    parts = [p.strip() for p in value.split('|') if p.strip()]
    if len(parts) <= 1:
        return value
    seen_lower = set()
    result = []
    for p in parts:
        pl = p.lower()
        if pl not in seen_lower:
            seen_lower.add(pl)
            result.append(p)
    return ' | '.join(result)
