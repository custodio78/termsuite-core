# Mejoras de Interfaz - Selector de Modo y Corpus Monolingüe

## Cambios a Realizar en `app/templates/index.html`

### 1. Agregar Selector de Modo (ANTES de la sección TMX, línea ~33)

**IMPORTANTE:** Solo agregar el selector, NO eliminar nada de la sección TMX existente.

Agregar ANTES de `<!-- Paso 1: Subir TMX -->`:

```html
<!-- Selector de Modo -->
<div class="card mb-4 shadow-sm" id="mode-selector">
    <div class="card-header bg-dark text-white">
        <h5 class="mb-0"><i class="fas fa-layer-group"></i> Selecciona el Tipo de Fuente</h5>
    </div>
    <div class="card-body">
        <div class="row">
            <div class="col-md-6 mb-3">
                <div class="card h-100 border-primary mode-card" style="cursor: pointer;" onclick="selectMode('tmx')">
                    <div class="card-body text-center">
                        <i class="fas fa-language fa-3x text-primary mb-3"></i>
                        <h5>Memoria TMX</h5>
                        <p class="text-muted small">Extrae términos de memorias de traducción bilingües o multilingües con traducciones</p>
                        <ul class="text-start small text-muted">
                            <li>Detección automática de idiomas</li>
                            <li>Múltiples traducciones</li>
                            <li>Búsqueda integrada</li>
                        </ul>
                        <span class="badge bg-primary">Recomendado</span>
                    </div>
                </div>
            </div>
            <div class="col-md-6 mb-3">
                <div class="card h-100 border-success mode-card" style="cursor: pointer;" onclick="selectMode('corpus')">
                    <div class="card-body text-center">
                        <i class="fas fa-file-alt fa-3x text-success mb-3"></i>
                        <h5>Corpus Monolingüe</h5>
                        <p class="text-muted small">Extrae términos técnicos de textos especializados en un solo idioma</p>
                        <ul class="text-start small text-muted">
                            <li>Análisis con TermSuite</li>
                            <li>Términos técnicos</li>
                            <li>Frecuencias y contextos</li>
                        </ul>
                        <span class="badge bg-success">Avanzado</span>
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>
```

### 2. Ocultar inicialmente la sección TMX

**IMPORTANTE:** Solo agregar `id` y `style`, NO cambiar nada más.

En la línea donde dice:
```html
<div class="card mb-4 shadow-sm">
    <div class="card-header bg-primary text-white">
        <h5 class="mb-0"><i class="fas fa-file-upload"></i> Extraer Términos de Memoria TMX</h5>
```

Cambiar SOLO la primera línea a:
```html
<div class="card mb-4 shadow-sm" id="tmx-section" style="display:none;">
    <div class="card-header bg-primary text-white">
        <h5 class="mb-0"><i class="fas fa-file-upload"></i> Extraer Términos de Memoria TMX</h5>
```

**TODO LO DEMÁS DE LA SECCIÓN TMX SE MANTIENE IGUAL:**
- Upload zone
- Selectores de idioma
- Checkbox de TermSuite
- Búsqueda
- Opciones de extracción
- Todo permanece intacto

### 3. Ocultar inicialmente la sección Corpus

En la línea donde dice:
```html
<div class="card mb-4 shadow-sm">
    <div class="card-header bg-success text-white">
        <h5 class="mb-0"><i class="fas fa-file-alt"></i> Extraer Términos de Corpus</h5>
```

Cambiar SOLO la primera línea a:
```html
<div class="card mb-4 shadow-sm" id="corpus-section" style="display:none;">
    <div class="card-header bg-success text-white">
        <h5 class="mb-0"><i class="fas fa-file-alt"></i> Extraer Términos de Corpus</h5>
```

**TODO LO DEMÁS DE LA SECCIÓN CORPUS SE MANTIENE IGUAL.**

### 4. Agregar JavaScript para el selector de modo

En el archivo `app/static/js/app.js`, agregar al FINAL (antes del último `}`):

```javascript
// Función para seleccionar modo
function selectMode(mode) {
    // Ocultar el selector de modo
    document.getElementById('mode-selector').style.display = 'none';
    
    // Ocultar ambas secciones
    document.getElementById('tmx-section').style.display = 'none';
    document.getElementById('corpus-section').style.display = 'none';
    
    // Mostrar la sección seleccionada
    if (mode === 'tmx') {
        document.getElementById('tmx-section').style.display = 'block';
        showToast('Modo: Memoria TMX seleccionado', 'info');
    } else if (mode === 'corpus') {
        document.getElementById('corpus-section').style.display = 'block';
        showToast('Modo: Corpus Monolingüe seleccionado', 'info');
    }
    
    // Scroll suave a la sección
    setTimeout(() => {
        const section = document.getElementById(mode + '-section');
        section.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }, 100);
}
```

**IMPORTANTE:** Esta función NO modifica ninguna funcionalidad existente de TMX. Solo muestra/oculta secciones.

### 6. Agregar estilos CSS en `app/static/css/style.css`

```css
/* Selector de modo */
.mode-card {
    transition: all 0.3s ease;
}

.mode-card:hover {
    transform: translateY(-5px);
    box-shadow: 0 8px 16px rgba(0,0,0,0.2);
}

.mode-card .card-body {
    padding: 2rem;
}

.mode-card i {
    transition: transform 0.3s ease;
}

.mode-card:hover i {
    transform: scale(1.1);
}
```

## Agregar Información de Idiomas en la Barra Lateral

### En la sección "Ayuda Rápida", agregar:

```html
<h6 class="mt-3">Idiomas Soportados (TreeTagger):</h6>
<div class="small">
    <strong>Instalados:</strong>
    <ul class="mb-2">
        <li>🇪🇸 Español</li>
        <li>🇬🇧 Inglés</li>
        <li>🇫🇷 Francés</li>
        <li>🇩🇪 Alemán</li>
        <li>🇵🇹 Portugués</li>
        <li>🇮🇹 Italiano</li>
    </ul>
    <strong>Disponibles para instalar:</strong>
    <p class="text-muted mb-0">
        40+ idiomas adicionales incluyendo holandés, ruso, polaco, chino, japonés, árabe, y más.
        <a href="#" data-bs-toggle="tooltip" title="Ver treetagger/DOWNLOAD_LINKS.md para la lista completa">
            <i class="fas fa-info-circle"></i>
        </a>
    </p>
</div>
```

## Resultado Final

Después de estos cambios:

1. **Pantalla inicial**: Muestra dos tarjetas grandes para elegir entre TMX o Corpus
2. **Al hacer click en TMX**: 
   - Se oculta el selector
   - Se muestra la sección TMX completa
   - **TODA la funcionalidad TMX funciona igual:**
     - Subir TMX
     - Detectar idiomas
     - Seleccionar idioma origen y destino
     - Checkbox TermSuite
     - Búsqueda de términos
     - Opciones de extracción
     - Exportar a Excel
3. **Al hacer click en Corpus**: Se muestra la sección de corpus monolingüe
4. **Información clara**: Los usuarios entienden qué opción elegir
5. **Idiomas documentados**: Los usuarios saben qué idiomas están disponibles

## Vista Previa del Flujo TMX (SIN CAMBIOS)

```
1. Usuario abre la aplicación
   ↓
2. Ve dos opciones:
   [Memoria TMX]  [Corpus Monolingüe]
   ↓
3. Click en "Memoria TMX"
   ↓
4. Se muestra la sección TMX completa (igual que antes)
   ↓
5. Sube TMX → Detecta idiomas → Selecciona idiomas
   ↓
6. Aplica idiomas → Configura opciones → Extrae
   ↓
7. Descarga Excel con múltiples traducciones
```

**TODO EL FLUJO TMX PERMANECE IDÉNTICO, solo se agrega un paso inicial de selección.**

## Notas

- El selector de modo mejora la UX al no mostrar ambas opciones simultáneamente
- Los usuarios novatos elegirán TMX (recomendado)
- Los usuarios avanzados pueden usar Corpus monolingüe
- La información de idiomas ayuda a saber qué está disponible
