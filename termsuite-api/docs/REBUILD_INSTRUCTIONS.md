# 🚀 Instrucciones para Reconstruir Docker

## Nueva Funcionalidad Implementada

Se ha añadido **clasificación de términos por ámbito/dominio** que permite:
- Describir el ámbito específico de trabajo
- Clasificar automáticamente términos por relevancia al dominio
- Nuevas columnas en Excel: "Relevancia Ámbito", "Confianza Ámbito", "Razón Ámbito"

## 📋 Pasos para Reconstruir

### Opción 1: Script Automático (Recomendado)

#### En Windows:
```cmd
cd termsuite-api
rebuild-docker.bat
```

#### En Linux/Mac:
```bash
cd termsuite-api
chmod +x rebuild-docker.sh
./rebuild-docker.sh
```

### Opción 2: Manual

```bash
cd termsuite-api

# Detener contenedor existente
docker-compose down

# Reconstruir imagen (sin caché para asegurar cambios)
docker-compose build --no-cache

# Iniciar contenedor
docker-compose up -d

# Verificar que funciona
curl http://localhost:7000/api
```

## 🔍 Verificar Cambios

Después de reconstruir, ejecuta el script de verificación:

```bash
python verify-changes.py
```

Este script verifica:
- ✅ API básica funcionando
- ✅ Nuevo endpoint de clasificación
- ✅ Integración con Ollama
- ✅ Cambios en frontend

## 🎯 Probar Nueva Funcionalidad

### 1. Interfaz Web
1. Abre http://localhost:7000
2. Sube un archivo TMX
3. En "Ámbito de Especialización":
   - Describe tu dominio (ej: "medicina cardiovascular")
   - Activa "Clasificar términos por relevancia al ámbito"
4. Procesa normalmente
5. Descarga Excel con nuevas columnas

### 2. API Directa
```bash
python test_domain_classification.py
```

### 3. Endpoint Manual
```bash
curl -X POST http://localhost:7000/api/ollama/classify-domain \
  -H "Content-Type: application/json" \
  -d '{
    "terms": ["algoritmo", "usuario", "cardiovascular"],
    "domain_description": "medicina cardiovascular",
    "language": "es"
  }'
```

## 📊 Nuevas Columnas en Excel

| Columna | Descripción | Ejemplo |
|---------|-------------|---------|
| **Relevancia Ámbito** | Si pertenece al dominio | "Sí", "No", "Incierto" |
| **Confianza Ámbito** | Porcentaje de confianza | "95%", "40%" |
| **Razón Ámbito** | Explicación breve | "Término específico del dominio médico" |

## 🔧 Solución de Problemas

### Contenedor no inicia
```bash
# Ver logs
docker-compose logs termsuite-api

# Verificar estado
docker-compose ps
```

### API no responde
```bash
# Verificar puerto
netstat -an | grep 7000

# Reiniciar contenedor
docker-compose restart
```

### Ollama no disponible
- Verifica que Ollama esté ejecutándose
- Revisa variables de entorno en docker-compose.yml:
  ```yaml
  environment:
    - OLLAMA_HOST=tu-host-ollama
    - OLLAMA_PORT=11434
  ```

### Cambios no se ven
```bash
# Reconstruir sin caché
docker-compose build --no-cache

# Limpiar imágenes anteriores
docker rmi termsuite-api-termsuite-api
docker-compose build
```

## 📁 Archivos Nuevos Creados

- `app/services/ollama_translator.py` - Funciones de clasificación añadidas
- `app/models.py` - Modelo `DomainClassificationRequest` añadido
- `app/main.py` - Endpoint `/api/ollama/classify-domain` añadido
- `app/templates/index_v2.html` - Sección "Ámbito de Especialización"
- `app/static/js/app_v2.js` - Manejo de configuración de dominio
- `test_domain_classification.py` - Script de pruebas
- `CLASIFICACION_AMBITO.md` - Documentación completa
- `RESUMEN_CLASIFICACION_AMBITO.md` - Resumen de implementación

## 🎉 Resultado Esperado

Después de reconstruir exitosamente:

1. **Interfaz Web**: Nueva sección "Ámbito de Especialización" visible
2. **API**: Endpoint `/api/ollama/classify-domain` disponible
3. **Excel**: 3 nuevas columnas de clasificación de dominio
4. **Integración**: Funciona con el flujo existente de traducciones

## 📞 Comandos Útiles

```bash
# Ver logs en tiempo real
docker-compose logs -f termsuite-api

# Reiniciar servicio
docker-compose restart

# Detener todo
docker-compose down

# Estado de contenedores
docker-compose ps

# Entrar al contenedor
docker-compose exec termsuite-api bash
```