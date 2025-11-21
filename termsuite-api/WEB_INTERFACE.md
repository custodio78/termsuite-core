# 🌐 Interfaz Web de TermSuite

Interfaz web moderna y fácil de usar para la extracción terminológica con TermSuite.

## 🚀 Acceso

Una vez que el contenedor Docker esté ejecutándose:

```
http://localhost:7000/
```

## ✨ Características

### 📋 Funcionalidades Principales

1. **Subir Memoria TMX**
   - Drag & drop o selección de archivo
   - Selección de idioma
   - Validación automática
   - Feedback en tiempo real

2. **Subir Corpus**
   - Soporta .txt y .zip
   - Drag & drop
   - Múltiples archivos en ZIP

3. **Configuración Avanzada**
   - Frecuencia mínima
   - Top N términos
   - Rango de palabras (min/max)
   - Ordenamiento personalizado
   - Formato de salida (Excel, CSV, JSON)
   - Incluir traducciones
   - Excluir números

4. **Dos Modos de Extracción**
   - **Del Corpus**: Extrae términos de documentos
   - **TMX Directo**: Exporta términos de la memoria TMX

5. **Resultados en Tiempo Real**
   - Barra de progreso animada
   - Estado actualizado automáticamente
   - Vista previa de resultados
   - Descarga directa

### 🎨 Diseño

- **Responsive**: Funciona en móvil, tablet y desktop
- **Moderno**: Diseño limpio con Bootstrap 5
- **Intuitivo**: Flujo de trabajo guiado paso a paso
- **Visual**: Iconos Font Awesome y colores distintivos

## 📱 Capturas de Pantalla

### Dashboard Principal
```
┌─────────────────────────────────────────┐
│  🔷 TermSuite                            │
├─────────────────────────────────────────┤
│  📁 Paso 1: Subir TMX                   │
│  [Drag & Drop Zone]                     │
│  Idioma: [es ▼]  [Subir]               │
│                                          │
│  📄 Paso 2: Subir Corpus                │
│  [Drag & Drop Zone]                     │
│  [Subir]                                │
│                                          │
│  ⚙️ Paso 3: Configurar                  │
│  Frecuencia: [2]  Top N: [100]         │
│  Palabras: [1] - [5]                    │
│  ☑ Traducciones  ☑ Excluir números     │
│  [🚀 Extraer] [📊 Exportar TMX]        │
│                                          │
│  📊 Resultados                           │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│  45% Procesando...                      │
└─────────────────────────────────────────┘
```

## 🎯 Flujo de Trabajo

### Opción A: Exportar TMX Directamente

1. Sube tu memoria TMX
2. Selecciona el idioma
3. Configura filtros (opcional)
4. Click en "Exportar TMX Directo"
5. Descarga el Excel

### Opción B: Extraer del Corpus

1. Sube tu memoria TMX (opcional)
2. Sube tu corpus (.txt o .zip)
3. Configura opciones de extracción
4. Click en "Extraer del Corpus"
5. Espera el procesamiento
6. Descarga los resultados

## 🔧 Componentes de la Interfaz

### Barra Superior
- Logo y título
- Link a documentación API

### Panel Principal (Izquierda)
- **Paso 1**: Upload TMX con drag & drop
- **Paso 2**: Upload Corpus con drag & drop
- **Paso 3**: Configuración completa
- **Resultados**: Barra de progreso y descarga
- **Vista Previa**: Top 10 términos

### Panel Lateral (Derecha)
- **Estado**: TMX, Corpus, Último trabajo
- **Ayuda**: Guía rápida de uso
- **Estadísticas**: Contadores en tiempo real

### Notificaciones
- Toast notifications en esquina inferior derecha
- Feedback inmediato de acciones

## 💻 Tecnologías Utilizadas

### Frontend
- **HTML5**: Estructura semántica
- **CSS3**: Estilos modernos con animaciones
- **JavaScript**: Lógica de aplicación (Vanilla JS)
- **Bootstrap 5**: Framework UI responsive
- **Font Awesome 6**: Iconos vectoriales

### Backend
- **FastAPI**: Servir HTML y archivos estáticos
- **Jinja2**: Motor de templates
- **Static Files**: CSS, JS, imágenes

## 📂 Estructura de Archivos

```
app/
├── static/
│   ├── css/
│   │   └── style.css          # Estilos personalizados
│   └── js/
│       └── app.js             # Lógica de la aplicación
├── templates/
│   └── index.html             # Página principal
└── main.py                    # Endpoints (modificado)
```

## 🎨 Personalización

### Cambiar Colores

Edita `app/static/css/style.css`:

```css
:root {
    --primary-color: #366092;    /* Azul principal */
    --success-color: #4CAF50;    /* Verde éxito */
    --warning-color: #FFC107;    /* Amarillo advertencia */
    --danger-color: #DC3545;     /* Rojo error */
}
```

### Agregar Logo

1. Coloca tu logo en `app/static/img/logo.png`
2. Edita `index.html`:

```html
<span class="navbar-brand mb-0 h1">
    <img src="/static/img/logo.png" height="30"> TermSuite
</span>
```

### Modificar Idiomas

Edita los `<select>` en `index.html`:

```html
<select id="tmx-language" class="form-select">
    <option value="es">Español</option>
    <option value="en">English</option>
    <!-- Agregar más idiomas -->
</select>
```

## 🐛 Troubleshooting

### La interfaz no carga

**Problema**: Error 404 al acceder a http://localhost:7000/

**Solución**:
```bash
# Verificar que el contenedor está corriendo
docker ps

# Ver logs
docker logs termsuite-api

# Reiniciar contenedor
docker restart termsuite-api
```

### Archivos estáticos no cargan

**Problema**: CSS/JS no se aplican

**Solución**:
```bash
# Verificar estructura de carpetas
ls -la app/static/css/
ls -la app/static/js/

# Reconstruir contenedor
docker-compose up --build
```

### Error al subir archivos

**Problema**: "Error de conexión"

**Solución**:
1. Verifica que el archivo sea válido (.tmx, .txt, .zip)
2. Verifica el tamaño del archivo (límite por defecto)
3. Revisa los logs del contenedor

### Barra de progreso no actualiza

**Problema**: Se queda en 0%

**Solución**:
1. Verifica que el JAR de TermSuite esté presente
2. Revisa los logs: `docker logs -f termsuite-api`
3. Verifica que el corpus sea válido

## 📊 Ejemplos de Uso

### Ejemplo 1: Exportar Términos de TMX

```
1. Abre http://localhost:7000/
2. Arrastra tu archivo ULMA_MasterTM.tmx al Paso 1
3. Selecciona idioma: "Español"
4. Click "Subir TMX"
5. Espera confirmación: "1,272 términos encontrados"
6. En Paso 3, configura:
   - Palabras: 1 - 5
   - ☑ Incluir traducciones
7. Click "Exportar TMX Directo"
8. Descarga automática del Excel
```

### Ejemplo 2: Extraer del Corpus

```
1. Sube TMX (opcional)
2. Sube corpus.zip en Paso 2
3. Configura en Paso 3:
   - Idioma: Español
   - Frecuencia mínima: 3
   - Top N: 100
   - ☑ Incluir traducciones
4. Click "Extraer del Corpus"
5. Observa barra de progreso
6. Cuando complete, click "Descargar Resultados"
```

## 🔐 Seguridad

### Consideraciones Actuales
- ✅ Validación de tipos de archivo
- ✅ Sanitización de inputs
- ⚠️ Sin autenticación (desarrollo)

### Para Producción
- [ ] Agregar autenticación de usuarios
- [ ] Implementar rate limiting
- [ ] Usar HTTPS
- [ ] Validar tamaños de archivo
- [ ] Sanitizar nombres de archivo

## 🚀 Mejoras Futuras

### Funcionalidades Planeadas
- [ ] Vista previa de términos antes de descargar
- [ ] Gráficos de distribución de frecuencias
- [ ] Comparación de dos extracciones
- [ ] Historial de trabajos
- [ ] Exportar/importar configuraciones
- [ ] Modo oscuro
- [ ] Búsqueda en resultados
- [ ] Filtros en tiempo real

### Optimizaciones
- [ ] WebSockets para progreso en tiempo real
- [ ] Cache de resultados
- [ ] Compresión de respuestas
- [ ] Lazy loading de resultados grandes

## 📝 Notas

- La interfaz usa la API REST existente
- No requiere configuración adicional
- Compatible con todos los navegadores modernos
- Funciona offline una vez cargada (excepto llamadas API)

## 🆘 Soporte

Para problemas o sugerencias:
1. Revisa los logs: `docker logs termsuite-api`
2. Consulta la documentación API: http://localhost:7000/docs
3. Verifica la configuración en `docker-compose.yml`
