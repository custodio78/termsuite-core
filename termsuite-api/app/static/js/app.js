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
            const select = document.getElementById('tmx-language-select');
            select.innerHTML = '';
            
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
            
            data.available_languages.forEach(lang => {
                const option = document.createElement('option');
                option.value = lang;
                option.textContent = `${langNames[lang] || lang.toUpperCase()} (${lang})`;
                select.appendChild(option);
            });
            
            showToast(`Idiomas detectados: ${data.available_languages.join(', ')}`, 'info');
        }
    } catch (error) {
        console.error('Error al cargar idiomas:', error);
    }
}

// Seleccionar idioma del TMX y extraer términos
async function selectTMXLanguage() {
    const language = document.getElementById('tmx-language-select').value;
    
    if (!language) {
        showToast('Selecciona un idioma', 'warning');
        return;
    }
    
    showToast(`Extrayendo términos en ${language}...`, 'info');
    
    try {
        const response = await fetch(`${API_BASE}/api/extract-tmx-language?tmx_id=${state.tmxId}&language=${language}`, {
            method: 'POST'
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showToast(data.message, 'success');
            updateStats('tmx', data.message);
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
    return {
        language: document.getElementById('extract-language').value,
        minFrequency: parseInt(document.getElementById('min-frequency').value) || null,
        topN: parseInt(document.getElementById('top-n').value) || null,
        minWords: parseInt(document.getElementById('min-words').value) || null,
        maxWords: parseInt(document.getElementById('max-words').value) || null,
        sortBy: document.getElementById('sort-by').value,
        format: document.getElementById('format').value,
        includeTranslation: document.getElementById('include-translation').checked,
        excludeNumbers: document.getElementById('exclude-numbers').checked
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
