# 🔍 DEBUG TERMSUITE-API

Esta carpeta contiene archivos de debugging, análisis y archivos temporales de desarrollo.

## 🐛 **SCRIPTS DE DEBUG**

### **Debug de Funcionalidades Principales**
- `debug_tmx.py` - Debug de procesamiento TMX
- `debug_termsuite.py` - Debug de TermSuite
- `debug_new_tmx.py` - Debug de nuevas funcionalidades TMX
- `debug_async_export.py` - Debug de exportación asíncrona
- `debug_frontend_flow.py` - Debug del flujo frontend

---

## 📊 **ARCHIVOS TEMPORALES DE DEBUG**

### **Archivos Excel de Debug**
- `debug_export_*.xlsx` - Archivos Excel generados durante debugging
- `test_*.xlsx` - Archivos de test de exportación
- `test_frontend_syntax.html` - Test de sintaxis frontend

---

## 🔧 **CÓMO USAR LOS SCRIPTS DE DEBUG**

### **Debug de TMX**
```bash
# Debug general de TMX
python debug/debug_tmx.py

# Debug de nuevas funcionalidades TMX
python debug/debug_new_tmx.py
```

### **Debug de TermSuite**
```bash
# Debug de TermSuite
python debug/debug_termsuite.py
```

### **Debug de Exportación**
```bash
# Debug de exportación asíncrona
python debug/debug_async_export.py
```

### **Debug de Frontend**
```bash
# Debug del flujo frontend
python debug/debug_frontend_flow.py
```

---

## 📋 **PROPÓSITO DE CADA SCRIPT**

### **`debug_tmx.py`**
- Analiza procesamiento de archivos TMX
- Verifica extracción de términos
- Debug de traducciones TMX

### **`debug_termsuite.py`**
- Debug de integración con TermSuite
- Verifica extracción de términos técnicos
- Analiza resultados de TermSuite

### **`debug_new_tmx.py`**
- Debug de nuevas funcionalidades TMX
- Prueba mejoras recientes
- Verifica compatibilidad

### **`debug_async_export.py`**
- Debug de exportación asíncrona
- Analiza trabajos en background
- Verifica progreso de exportación

### **`debug_frontend_flow.py`**
- Debug del flujo frontend-backend
- Verifica comunicación API
- Analiza respuestas del servidor

---

## 🔍 **ANÁLISIS DE ARCHIVOS TEMPORALES**

### **Archivos Excel de Debug**
Los archivos `debug_export_*.xlsx` contienen:
- Resultados de exportaciones de prueba
- Datos para análisis de formato
- Verificación de columnas y contenido

### **Archivos de Test**
Los archivos `test_*.xlsx` son:
- Resultados de tests específicos
- Comparaciones de métodos
- Verificaciones de funcionalidad

---

## 📊 **INTERPRETACIÓN DE RESULTADOS**

### **Salida Típica de Debug**
```
🔍 DEBUG: Iniciando análisis TMX...
✅ TMX cargado: 150 términos encontrados
⚠️  Advertencia: 5 términos sin traducción
❌ Error: Fallo en clasificación de 2 términos
📊 Resumen: 143/150 términos procesados correctamente
```

### **Códigos de Estado**
- ✅ **Éxito**: Operación completada correctamente
- ⚠️ **Advertencia**: Operación completada con problemas menores
- ❌ **Error**: Operación falló
- 🔍 **Info**: Información de debug
- 📊 **Resumen**: Estadísticas finales

---

## 🧹 **LIMPIEZA DE ARCHIVOS DEBUG**

### **Archivos Seguros para Eliminar**
```bash
# Eliminar archivos Excel temporales
rm debug/debug_export_*.xlsx
rm debug/test_*.xlsx

# Eliminar archivos HTML temporales
rm debug/*.html
```

### **Archivos a Conservar**
- `debug_*.py` - Scripts de debug (conservar)
- `README_DEBUG.md` - Esta documentación (conservar)

---

## 🔧 **CONFIGURACIÓN DE DEBUG**

### **Variables de Debug**
Los scripts de debug usan estas configuraciones:
```python
DEBUG_MODE = True
API_BASE = "http://localhost:7000"
VERBOSE_OUTPUT = True
SAVE_TEMP_FILES = True
```

### **Niveles de Debug**
- **BASIC**: Solo errores críticos
- **VERBOSE**: Información detallada
- **FULL**: Todo el flujo paso a paso

---

## 📝 **CREAR NUEVOS SCRIPTS DE DEBUG**

### **Plantilla Básica**
```python
#!/usr/bin/env python3
"""
Script de debug para [funcionalidad]
"""

import requests
import json
from pathlib import Path

# Configuración
API_BASE = "http://localhost:7000"
DEBUG_MODE = True

def debug_funcionalidad():
    """Debug de funcionalidad específica"""
    print("🔍 DEBUG: Iniciando análisis...")
    
    try:
        # Tu código de debug aquí
        print("✅ Debug completado exitosamente")
    except Exception as e:
        print(f"❌ Error en debug: {str(e)}")

if __name__ == "__main__":
    debug_funcionalidad()
```

---

**💡 Tip**: Usa los scripts de debug cuando encuentres problemas específicos o quieras analizar el comportamiento de una funcionalidad en detalle.