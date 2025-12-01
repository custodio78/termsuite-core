// Estado global
let state = {
    tmxId: null,
    corpusId: null,
    jobId: null,
    downloadUrl: null
};

// API Base URL
const API_BASE = '';

// Inicialización
document.addEventListener('DOMContentLoaded', function() {
    setupDragAndDrop();
    setupFileInputs();
    
    // Inicializar tooltips de Bootstrap
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
});

// Setup Drag and Drop
function setupDragAndDrop() {
    const tmxZone = document.getElementById('tmx-dropzone');
    const corpusZone = document.getElementById('corpus-dropzone');
    
    [tmxZone, corpusZone].forEach(zone => {
        zone.addEventListener('dragover', (e) => {
            e.preventDefault();
            zone.classList.add('dragover');
        });
        
        zone.addEventListener('dragleave', () => {
            zone.classList.remove('dragover');
        });
        
        zone.addEventListener('drop', (e) => {
            e.preventDefault();
            zone.classList.remove('dragover');
            
            const files = e.dataTransfer.files;
            if (files.length > 0) {
                if (zone.id === 'tmx-dropzone') {
                    document.getElementById('tmx-file').files = files;
                } else {
                    document.getElementById('corpus-file').files = files;
                }
            }
        });
    });
}

// Setup File Inputs
function setupFileInputs() {
    document.getElementById('tmx-file').addEventListener('change', function(e) {
        if (e.target.files.length > 0) {
            showToast(`Archivo seleccionado: ${e.target.files[0].name}`, 'info');
        }
    });
    
    document.getElementById('corpus-file').addEventListener('change', function(e) {
        if (e.target.files.length > 0) {
            showToast(`Archivo seleccionado: ${e.target.files[0].name}`, 'info');
        }
    });
}

// Upload TMX
async function uploadTMX() {
    const fileInput = document.getElementById('tmx-file');
    
    if (!fileInput.files || fileInput.files.length === 0) {
        showToast('Por favor selecciona un archivo TMX', 'warning');
        return;
    }
    
    const file = fileInput.files[0];
    if (!file.name.endsWith('.tmx')) {
        showToast('El archivo debe ser .tmx', 'error');
        return;
    }
    
    const formData = new FormData();
    formData.append('file', file);
    
    const btn = document.getElementById('btn-upload-tmx');
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner"></span> Analizando TMX...';
    
    try {
        // Subir sin idioma para obtener idiomas disponibles
        const response = await fetch(`${API_BASE}/api/upload-tmx`, {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (response.ok) {
            state.tmxId = data.file_id;
            showStatus('tmx', 'success', data.message);
            showToast('TMX subido exitosamente', 'success');
            
            // Obtener idiomas disponibles
            await loadTMXLanguages(data.file_id);
            
            // Mostrar opciones de extracción TMX
            document.getElementById('tmx-extract-options').style.display = 'block';
        } else {
            showToast(`Error: ${data.detail}`, 'error');
        }
    } catch (error) {
        showToast(`Error de conexión: ${error.message}`, 'error');
    } finally {
        btn.disabled = false;
        btn.innerHTML = '<i class="fas fa-upload"></i> Subir TMX';
    }
}

// Cargar idiomas disponibles del TMX
async function loadTMXLanguages(tmxId) {
    try {
        const response = await fetch(`${API_BASE}/api/tmx-languages/${tmxId}`);
        const data = await response.json();
        
        if (response.ok && data.available_languages) {
            const sourceSelect = document.getElementById('tmx-language-select');
            const targetSelect = document.getElementById('tmx-target-language-select');
            const targetContainer = document.getElementById('tmx-target-language-container');
            
            sourceSelect.innerHTML = '';
            targetSelect.innerHTML = '';
            
            // Mapeo de códigos a nombres
            const langNames = {
                'es': 'Español',
                'en': 'English',
                'fr': 'Français',
                'de': 'Deutsch',
                'it': 'Italiano',
                'pt': 'Português',
                'eu': 'Euskara',
                'ca': 'Català',
                'gl': 'Galego'
            };
            
            // Llenar selector de idioma origen
            data.available_languages.forEach(lang => {
                const option = document.createElement('option');
                option.value = lang;
                option.textContent = `${langNames[lang] || lang.toUpperCase()} (${lang})`;
                sourceSelect.appendChild(option);
            });
            
            // Si hay más de un idioma, mostrar selector de idioma destino
            if (data.available_languages.length > 1) {
                targetContainer.style.display = 'block';
                
                // Llenar selector de idioma destino
                data.available_languages.forEach(lang => {
                    const option = document.createElement('option');
                    option.value = lang;
                    option.textContent = `${langNames[lang] || lang.toUpperCase()} (${lang})`;
                    targetSelect.appendChild(option);
                });
                
                // Seleccionar automáticamente el segundo idioma como destino
                if (data.available_languages.length >= 2) {
                    targetSelect.value = data.available_languages[1];
                }
                
                showToast(`TMX multiidioma detectado: ${data.available_languages.join(', ')}`, 'info');
            } else {
                targetContainer.style.display = 'none';
                showToast(`Idioma detectado: ${data.available_languages.join(', ')}`, 'info');
            }
        }
    } catch (error) {
        console.error('Error al cargar idiomas:', error);
    }
}

// Seleccionar idioma del TMX y extraer términos
async function selectTMXLanguage() {
    const sourceLanguage = document.getElementById('tmx-language-select').value;
    const targetLanguage = document.getElementById('tmx-target-language-select').value;
    const targetContainer = document.getElementById('tmx-target-language-container');
    
    if (!sourceLanguage) {
        showToast('Selecciona un idioma origen', 'warning');
        return;
    }
    
    // Validar que los idiomas sean diferentes si hay selector de destino visible
    if (targetContainer.style.display !== 'none' && sourceLanguage === targetLanguage) {
        showToast('Los idiomas origen y destino deben ser diferentes', 'warning');
        return;
    }
    
    const langMsg = targetContainer.style.display !== 'none' 
        ? `${sourceLanguage} → ${targetLanguage}` 
        : sourceLanguage;
    
    const useTermSuite = document.getElementById('tmx-use-termsuite').checked;
    const modeMsg = useTermSuite ? ' (con TermSuite)' : '';
    
    showToast(`Extrayendo términos: ${langMsg}${modeMsg}...`, 'info');
    
    try {
        let url = `${API_BASE}/api/extract-tmx-language?tmx_id=${state.tmxId}&language=${sourceLanguage}`;
        
        // Agregar idioma destino si está visible
        if (targetContainer.style.display !== 'none') {
            url += `&target_language=${targetLanguage}`;
        }
        
        // Agregar modo TermSuite
        if (useTermSuite) {
            url += `&use_termsuite=true`;
        }
        
        const response = await fetch(url, {
            method: 'POST'
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showToast(data.message, 'success');
            updateStats('tmx', data.message);
            
            // Actualizar etiqueta de traducción si hay idioma destino
            if (targetContainer.style.display !== 'none') {
                const translationLabel = document.getElementById('tmx-translation-label');
                translationLabel.textContent = `Incluir traducciones (${sourceLanguage} → ${targetLanguage})`;
            }
        } else {
            showToast(`Error: ${data.detail}`, 'error');
        }
    } catch (error) {
        showToast(`Error: ${error.message}`, 'error');
    }
}

// Upload Corpus
async function uploadCorpus() {
    const fileInput = document.getElementById('corpus-file');
    
    if (!fileInput.files || fileInput.files.length === 0) {
        showToast('Por favor selecciona un archivo', 'warning');
        return;
    }
    
    const file = fileInput.files[0];
    const validExtensions = ['.txt', '.zip'];
    const isValid = validExtensions.some(ext => file.name.endsWith(ext));
    
    if (!isValid) {
        showToast('El archivo debe ser .txt o .zip', 'error');
        return;
    }
    
    const formData = new FormData();
    formData.append('file', file);
    
    const btn = document.getElementById('btn-upload-corpus');
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner"></span> Subiendo...';
    
    try {
        const response = await fetch(`${API_BASE}/api/upload-corpus`, {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (response.ok) {
            state.corpusId = data.file_id;
            showStatus('corpus', 'success', data.message);
            showToast('Corpus subido exitosamente', 'success');
            // Mostrar opciones de extracción Corpus
            document.getElementById('corpus-extract-options').style.display = 'block';
        } else {
            showToast(`Error: ${data.detail}`, 'error');
        }
    } catch (error) {
        showToast(`Error de conexión: ${error.message}`, 'error');
    } finally {
        btn.disabled = false;
        btn.innerHTML = '<i class="fas fa-upload"></i> Subir Corpus';
    }
}

// Extract from Corpus
async function extractFromCorpus() {
    if (!state.corpusId) {
        showToast('Primero debes subir un corpus', 'warning');
        return;
    }
    
    const config = getExtractionConfig();
    const payload = {
        corpus_id: state.corpusId,
        language: config.language,
        min_frequency: config.minFrequency,
        use_tmx: state.tmxId !== null,
        tmx_id: state.tmxId
    };
    
    const btn = document.getElementById('btn-extract-corpus');
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner"></span> Extrayendo...';
    
    showResults('processing');
    
    try {
        const response = await fetch(`${API_BASE}/api/extract`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        
        const data = await response.json();
        
        if (response.ok) {
            state.jobId = data.job_id;
            showToast('Extracción iniciada', 'info');
            pollJobStatus();
        } else {
            showResults('error', data.detail);
            showToast(`Error: ${data.detail}`, 'error');
        }
    } catch (error) {
        showResults('error', error.message);
        showToast(`Error: ${error.message}`, 'error');
    } finally {
        btn.disabled = false;
        btn.innerHTML = '<i class="fas fa-rocket"></i> Extraer del Corpus';
    }
}

// Extract from TMX
async function extractFromTMX() {
    if (!state.tmxId) {
        showToast('Primero debes subir un TMX', 'warning');
        return;
    }
    
    // Usar configuración específica del TMX
    const params = new URLSearchParams({
        min_frequency: document.getElementById('tmx-min-frequency').value || '',
        top_n: document.getElementById('tmx-top-n').value || '',
        min_words: document.getElementById('tmx-min-words').value || '',
        max_words: document.getElementById('tmx-max-words').value || '',
        sort_by: 'frequency',
        format: 'excel',
        exclude_numbers: document.getElementById('tmx-exclude-numbers').checked,
        include_translation: document.getElementById('tmx-include-translation').checked
    });
    
    // Remover parámetros vacíos
    for (let [key, value] of [...params.entries()]) {
        if (!value || value === 'false') {
            params.delete(key);
        }
    }
    
    const url = `${API_BASE}/api/export/tmx-excel/${state.tmxId}?${params.toString()}`;
    
    const btn = document.getElementById('btn-extract-tmx');
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner"></span> Extrayendo...';
    
    try {
        // Descargar directamente
        window.location.href = url;
        showToast('Descarga iniciada', 'success');
        
        setTimeout(() => {
            btn.disabled = false;
            btn.innerHTML = '<i class="fas fa-file-export"></i> Extraer del TMX';
        }, 2000);
    } catch (error) {
        showToast(`Error: ${error.message}`, 'error');
        btn.disabled = false;
        btn.innerHTML = '<i class="fas fa-file-export"></i> Extraer del TMX';
    }
}

// Poll Job Status
async function pollJobStatus() {
    const interval = setInterval(async () => {
        try {
            const response = await fetch(`${API_BASE}/api/status/${state.jobId}`);
            const data = await response.json();
            
            updateProgress(data.progress, data.message);
            
            if (data.status === 'completed') {
                clearInterval(interval);
                state.downloadUrl = `/api/export/excel/${state.jobId}`;
                showResults('success', `Completado: ${data.message}`);
                showToast('Extracción completada', 'success');
                updateStats('extracted', 'Términos extraídos');
            } else if (data.status === 'failed') {
                clearInterval(interval);
                showResults('error', data.error || 'Error desconocido');
                showToast('Extracción fallida', 'error');
            }
        } catch (error) {
            clearInterval(interval);
            showResults('error', error.message);
        }
    }, 2000);
}

// Get Extraction Config
function getExtractionConfig() {
    const languageElement = document.getElementById('extract-language');
    const minFreqElement = document.getElementById('min-frequency');
    const topNElement = document.getElementById('top-n');
    const minWordsElement = document.getElementById('min-words');
    const maxWordsElement = document.getElementById('max-words');
    const sortByElement = document.getElementById('sort-by');
    const formatElement = document.getElementById('format');
    const includeTransElement = document.getElementById('include-translation');
    const excludeNumElement = document.getElementById('exclude-numbers');
    
    return {
        language: languageElement ? languageElement.value : 'es',
        minFrequency: minFreqElement ? (parseInt(minFreqElement.value) || null) : null,
        topN: topNElement ? (parseInt(topNElement.value) || null) : null,
        minWords: minWordsElement ? (parseInt(minWordsElement.value) || null) : null,
        maxWords: maxWordsElement ? (parseInt(maxWordsElement.value) || null) : null,
        sortBy: sortByElement ? sortByElement.value : 'frequency',
        format: formatElement ? formatElement.value : 'excel',
        includeTranslation: includeTransElement ? includeTransElement.checked : false,
        excludeNumbers: excludeNumElement ? excludeNumElement.checked : false
    };
}

// Show Results
function showResults(status, message = '') {
    const card = document.getElementById('results-card');
    const progressContainer = document.getElementById('progress-container');
    const successContainer = document.getElementById('results-success');
    const errorContainer = document.getElementById('results-error');
    
    card.style.display = 'block';
    card.classList.add('fade-in');
    
    progressContainer.style.display = 'none';
    successContainer.style.display = 'none';
    errorContainer.style.display = 'none';
    
    if (status === 'processing') {
        progressContainer.style.display = 'block';
    } else if (status === 'success') {
        successContainer.style.display = 'block';
        document.getElementById('results-message').textContent = message;
    } else if (status === 'error') {
        errorContainer.style.display = 'block';
        document.getElementById('error-message').textContent = message;
    }
}

// Update Progress
function updateProgress(percent, message) {
    document.getElementById('progress-bar').style.width = `${percent}%`;
    document.getElementById('progress-percent').textContent = `${percent}%`;
    document.getElementById('progress-text').textContent = message;
}

// Download Results
function downloadResults() {
    if (state.downloadUrl) {
        window.location.href = state.downloadUrl;
        showToast('Descarga iniciada', 'success');
    }
}

// Show Status
function showStatus(type, status, message) {
    const statusElement = document.getElementById(`status-${type}`);
    const statusDiv = document.getElementById(`${type}-status`);
    const statusText = document.getElementById(`${type}-status-text`);
    
    if (status === 'success') {
        statusElement.className = 'badge bg-success';
        statusElement.textContent = 'Subido';
        statusDiv.className = 'alert alert-success mt-3';
        statusDiv.style.display = 'block';
        statusText.textContent = message;
    }
}

// Update Stats
function updateStats(type, message) {
    if (type === 'tmx') {
        const match = message.match(/(\d+)\s+términos/);
        if (match) {
            document.getElementById('stat-tmx-terms').textContent = match[1];
        }
    }
}

// Debug TMX - Buscar término específico
async function debugTMX() {
    if (!state.tmxId) {
        showToast('Primero debes subir un TMX', 'warning');
        return;
    }
    
    const searchTerm = document.getElementById('tmx-search-term').value.trim();
    
    if (!searchTerm) {
        showToast('Ingresa un término a buscar', 'warning');
        return;
    }
    
    showToast(`Buscando "${searchTerm}" en TMX...`, 'info');
    
    try {
        const response = await fetch(`${API_BASE}/api/tmx-debug/${state.tmxId}?search=${encodeURIComponent(searchTerm)}`);
        const data = await response.json();
        
        if (response.ok) {
            // Mostrar resultados en el panel integrado
            displaySearchResults(searchTerm, data);
            
            // También en consola para debugging
            console.log('Resultados de búsqueda:', data);
            
        } else {
            showToast(`Error: ${data.detail}`, 'error');
        }
    } catch (error) {
        showToast(`Error: ${error.message}`, 'error');
    }
}

// Mostrar resultados de búsqueda en panel integrado
function displaySearchResults(searchTerm, data) {
    const resultsContainer = document.getElementById('search-results');
    const resultsBody = document.getElementById('search-results-body');
    const termDisplay = document.getElementById('search-term-display');
    
    // Mostrar el término buscado
    termDisplay.textContent = `"${searchTerm}"`;
    
    // Construir HTML de resultados
    let html = '';
    
    for (const [lang, info] of Object.entries(data.details)) {
        if (info.search) {
            const langName = getLangName(lang);
            
            if (info.search.exact_match) {
                // Coincidencia exacta
                html += `
                    <div class="alert alert-success mb-2 py-2">
                        <div class="d-flex align-items-center">
                            <i class="fas fa-check-circle me-2"></i>
                            <div class="flex-grow-1">
                                <strong>${langName} (${lang})</strong>: Encontrado
                            </div>
                            <span class="badge bg-success">${info.search.frequency}x</span>
                        </div>
                    </div>
                `;
            } else if (info.search.partial_matches.length > 0) {
                // Coincidencias parciales
                html += `
                    <div class="alert alert-warning mb-2 py-2">
                        <div class="d-flex align-items-center mb-1">
                            <i class="fas fa-exclamation-triangle me-2"></i>
                            <div class="flex-grow-1">
                                <strong>${langName} (${lang})</strong>: ${info.search.partial_matches.length} coincidencias parciales
                            </div>
                        </div>
                        <small class="ms-4">
                `;
                
                info.search.partial_matches.slice(0, 5).forEach(m => {
                    html += `
                        <div class="d-flex justify-content-between align-items-center mt-1">
                            <span class="text-muted">"${m.term}"</span>
                            <span class="badge bg-warning text-dark">${m.frequency}x</span>
                        </div>
                    `;
                });
                
                if (info.search.partial_matches.length > 5) {
                    html += `<div class="text-muted mt-1">... y ${info.search.partial_matches.length - 5} más</div>`;
                }
                
                html += `
                        </small>
                    </div>
                `;
            } else {
                // No encontrado
                html += `
                    <div class="alert alert-danger mb-2 py-2">
                        <div class="d-flex align-items-center">
                            <i class="fas fa-times-circle me-2"></i>
                            <div class="flex-grow-1">
                                <strong>${langName} (${lang})</strong>: No encontrado
                            </div>
                        </div>
                    </div>
                `;
            }
        }
    }
    
    // Agregar estadísticas generales
    html += `
        <div class="mt-2 p-2 bg-light rounded">
            <small class="text-muted">
                <strong>Estadísticas del TMX:</strong><br>
    `;
    
    for (const [lang, info] of Object.entries(data.details)) {
        const langName = getLangName(lang);
        html += `
            ${langName}: ${info.total_unique_terms.toLocaleString()} términos únicos, 
            ${info.total_occurrences.toLocaleString()} ocurrencias<br>
        `;
    }
    
    html += `
            </small>
        </div>
    `;
    
    resultsBody.innerHTML = html;
    resultsContainer.style.display = 'block';
    
    // Scroll suave al panel de resultados
    resultsContainer.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

// Obtener nombre legible del idioma
function getLangName(code) {
    const langNames = {
        'es': 'Español',
        'en': 'English',
        'fr': 'Français',
        'de': 'Deutsch',
        'it': 'Italiano',
        'pt': 'Português',
        'eu': 'Euskara',
        'ca': 'Català',
        'gl': 'Galego'
    };
    return langNames[code] || code.toUpperCase();
}

// Show Toast
function showToast(message, type = 'info') {
    const toast = document.getElementById('toast');
    const toastBody = document.getElementById('toast-body');
    const toastHeader = toast.querySelector('.toast-header');
    
    toastBody.textContent = message;
    
    // Cambiar color según tipo
    toastHeader.className = 'toast-header';
    if (type === 'success') {
        toastHeader.classList.add('bg-success', 'text-white');
    } else if (type === 'error') {
        toastHeader.classList.add('bg-danger', 'text-white');
    } else if (type === 'warning') {
        toastHeader.classList.add('bg-warning');
    } else {
        toastHeader.classList.add('bg-info', 'text-white');
    }
    
    const bsToast = new bootstrap.Toast(toast);
    bsToast.show();
}
