// Estado global
let state = {
    currentStep: 1,
    fileType: null, // 'tmx' or 'corpus'
    fileId: null,
    fileName: null,
    fileSize: null,
    availableLanguages: [],
    sourceLanguage: null,
    targetLanguage: null,
    config: {
        preset: 'standard',
        minFrequency: 2,
        minWords: 1,
        maxWords: 5,
        excludeNumbers: false,
        includeTranslations: true,
        useOllama: true
    }
};

const API_BASE = '';

// Clave para último análisis en localStorage
const LAST_ANALYSIS_KEY = 'linguaterms_last_analysis';

// Inicialización segura (funciona aunque DOMContentLoaded ya se haya disparado)
function initApp() {
    setupFileUpload();
    setupDragAndDrop();
    checkOllamaStatus();
    loadHistory();
    updateRecoveryVisibility();

    // Configurar event listener para botón de descarga
    const downloadBtn = document.getElementById('download-btn');
    if (downloadBtn) {
        downloadBtn.addEventListener('click', downloadResultsOptimized);
    }

    // También buscar por clase como fallback
    const downloadBtnByClass = document.querySelector('.btn-download');
    if (downloadBtnByClass && !downloadBtn) {
        downloadBtnByClass.addEventListener('click', downloadResultsOptimized);
    }
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initApp);
} else {
    // DOM ya está listo cuando se carga el script al final del body
    initApp();
}

// Setup File Upload
function setupFileUpload() {
    const fileInput = document.getElementById('tmx-file-input');
    fileInput.addEventListener('change', handleFileSelect);
}

// Setup Drag and Drop
function setupDragAndDrop() {
    const uploadZone = document.getElementById('upload-zone');
    
    uploadZone.addEventListener('click', () => {
        document.getElementById('tmx-file-input').click();
    });
    
    uploadZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadZone.classList.add('dragover');
    });
    
    uploadZone.addEventListener('dragleave', () => {
        uploadZone.classList.remove('dragover');
    });
    
    uploadZone.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadZone.classList.remove('dragover');
        
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            handleFile(files[0]);
        }
    });
}

// Handle File Select
function handleFileSelect(e) {
    const file = e.target.files[0];
    if (file) {
        handleFile(file);
    }
}

// Handle File
async function handleFile(file) {
    // Detect file type
    if (file.name.endsWith('.tmx')) {
        state.fileType = 'tmx';
    } else if (file.name.endsWith('.txt') || file.name.endsWith('.zip')) {
        state.fileType = 'corpus';
    } else {
        showToast('Formato no válido. Usa .tmx, .txt o .zip', 'error');
        return;
    }
    
    state.fileName = file.name;
    state.fileSize = formatFileSize(file.size);
    
    // Show preview
    const fileTypeLabel = state.fileType === 'tmx' ? 'Memoria TMX' : 'Corpus Monolingüe';
    document.getElementById('file-name').textContent = file.name;
    document.getElementById('file-info').textContent = `Tipo: ${fileTypeLabel} • Tamaño: ${state.fileSize}`;
    document.getElementById('file-preview').style.display = 'block';
    document.getElementById('upload-zone').style.display = 'none';
    
    // Upload file
    await uploadFile(file);
}

// Upload File
async function uploadFile(file) {
    const progressDiv = document.getElementById('upload-progress');
    const progressBar = document.getElementById('upload-progress-bar');
    const progressPercent = document.getElementById('upload-percent');
    
    progressDiv.style.display = 'block';
    
    const formData = new FormData();
    formData.append('file', file);
    
    try {
        // Simulate progress
        let progress = 0;
        const progressInterval = setInterval(() => {
            progress += 10;
            if (progress <= 90) {
                progressBar.style.width = progress + '%';
                progressPercent.textContent = progress + '%';
            }
        }, 200);
        
        // Upload to appropriate endpoint
        const endpoint = state.fileType === 'tmx' ? '/api/upload-tmx' : '/api/upload-corpus';
        const response = await fetch(`${API_BASE}${endpoint}`, {
            method: 'POST',
            body: formData
        });
        
        clearInterval(progressInterval);
        progressBar.style.width = '100%';
        progressPercent.textContent = '100%';
        
        const data = await response.json();
        
        if (response.ok) {
            state.fileId = data.file_id;
            
            if (state.fileType === 'tmx') {
                // Get available languages for TMX
                await loadLanguages(data.file_id);
            } else {
                // For corpus, show language selector
                await setupCorpusLanguages();
            }
            
            // Show analysis result
            setTimeout(() => {
                progressDiv.style.display = 'none';
                document.getElementById('file-analysis').style.display = 'block';
            }, 500);
        } else {
            throw new Error(data.detail || 'Error al subir el archivo');
        }
    } catch (error) {
        showToast(`Error: ${error.message}`, 'error');
        removeFile();
    }
}

// Load Languages
async function loadLanguages(tmxId) {
    try {
        const response = await fetch(`${API_BASE}/api/tmx-languages/${tmxId}`);
        const data = await response.json();
        
        if (response.ok && data.available_languages) {
            state.availableLanguages = data.available_languages;
            
            // Show detected languages
            const langNames = {
                'es': 'Español', 'en': 'English', 'fr': 'Français',
                'de': 'Deutsch', 'it': 'Italiano', 'pt': 'Português',
                'eu': 'Euskara', 'ca': 'Català', 'gl': 'Galego'
            };
            
            const langList = data.available_languages
                .map(lang => langNames[lang] || lang.toUpperCase())
                .join(', ');
            
            document.getElementById('detected-languages').innerHTML = `
                <strong>Idiomas detectados:</strong> ${langList}
            `;
            
            // Populate language selectors
            populateLanguageSelectors(data.available_languages, langNames);
        }
    } catch (error) {
        console.error('Error loading languages:', error);
    }
}

// Populate Language Selectors
function populateLanguageSelectors(languages, langNames) {
    const sourceSelect = document.getElementById('source-language');
    const targetSelect = document.getElementById('target-language');
    
    sourceSelect.innerHTML = '';
    targetSelect.innerHTML = '';
    
    languages.forEach((lang, index) => {
        const sourceName = langNames[lang] || lang.toUpperCase();
        const sourceOption = document.createElement('option');
        sourceOption.value = lang;
        sourceOption.textContent = `${sourceName} (${lang})`;
        sourceSelect.appendChild(sourceOption);
        
        const targetOption = document.createElement('option');
        targetOption.value = lang;
        targetOption.textContent = `${sourceName} (${lang})`;
        targetSelect.appendChild(targetOption);
    });
    
    // Set default selection - prioritize Spanish if available, otherwise first language
    if (languages.length >= 2) {
        // Prefer Spanish as source language if available
        const preferredSource = languages.includes('es') ? 'es' : languages[0];
        const preferredTarget = languages.find(lang => lang !== preferredSource) || languages[1];
        
        sourceSelect.value = preferredSource;
        targetSelect.value = preferredTarget;
        state.sourceLanguage = preferredSource;
        state.targetLanguage = preferredTarget;
    } else if (languages.length === 1) {
        sourceSelect.value = languages[0];
        state.sourceLanguage = languages[0];
        document.getElementById('target-language-container').style.display = 'none';
    }
}

// Setup Corpus Languages
async function setupCorpusLanguages() {
    const langNames = {
        'es': 'Español', 'en': 'English', 'fr': 'Français',
        'de': 'Deutsch', 'it': 'Italiano', 'pt': 'Português',
        'ru': 'Русский', 'da': 'Dansk', 'lv': 'Latviešu', 'zh': '中文'
    };
    
    // For corpus, show all supported languages
    const supportedLanguages = ['es', 'en', 'fr', 'de', 'it', 'ru', 'da', 'lv', 'zh'];
    state.availableLanguages = supportedLanguages;
    
    const sourceSelect = document.getElementById('source-language');
    sourceSelect.innerHTML = '';
    
    supportedLanguages.forEach(lang => {
        const option = document.createElement('option');
        option.value = lang;
        option.textContent = `${langNames[lang]} (${lang})`;
        sourceSelect.appendChild(option);
    });
    
    // Default to Spanish
    sourceSelect.value = 'es';
    state.sourceLanguage = 'es';
    
    // Hide target language for corpus
    document.getElementById('target-language-container').style.display = 'none';
    document.getElementById('include-translations').closest('.form-check').style.display = 'none';
    
    document.getElementById('detected-languages').innerHTML = `
        <strong>Tipo:</strong> Corpus Monolingüe<br>
        <strong>Selecciona el idioma del corpus en el siguiente paso</strong>
    `;
}

// Remove File
function removeFile() {
    document.getElementById('file-preview').style.display = 'none';
    document.getElementById('upload-zone').style.display = 'block';
    document.getElementById('tmx-file-input').value = '';
    state.fileId = null;
    state.fileName = null;
    updateRecoveryVisibility();
}

// Go to Step
function goToStep(step) {
    // Update step indicators
    for (let i = 1; i <= 3; i++) {
        const indicator = document.getElementById(`step-indicator-${i}`);
        const content = document.getElementById(`step-${i}`);
        
        indicator.classList.remove('active', 'completed');
        content.classList.remove('active');
        
        if (i < step) {
            indicator.classList.add('completed');
        } else if (i === step) {
            indicator.classList.add('active');
            content.classList.add('active');
        }
    }
    
    state.currentStep = step;
    window.scrollTo({ top: 0, behavior: 'smooth' });
    if (step === 1) {
        updateRecoveryVisibility();
    }
}

// Select Preset
function selectPreset(preset) {
    document.querySelectorAll('.config-preset').forEach(el => {
        el.classList.remove('active');
    });
    
    document.querySelector(`[data-preset="${preset}"]`).classList.add('active');
    
    state.config.preset = preset;
    
    // Update values based on preset
    const presets = {
        standard: { minFrequency: 2, minWords: 1, maxWords: 5 },
        exhaustive: { minFrequency: 1, minWords: 1, maxWords: 7 },
        selective: { minFrequency: 5, minWords: 2, maxWords: 4 }
    };
    
    const config = presets[preset];
    document.getElementById('min-frequency').value = config.minFrequency;
    document.getElementById('min-words').value = config.minWords;
    document.getElementById('max-words').value = config.maxWords;
    updateFreqValue(config.minFrequency);
    
    state.config.minFrequency = config.minFrequency;
    state.config.minWords = config.minWords;
    state.config.maxWords = config.maxWords;
}

// Update Frequency Value
function updateFreqValue(value) {
    document.getElementById('freq-value').textContent = value;
    state.config.minFrequency = parseInt(value);
}

// Start Extraction
async function startExtraction() {
    // Get current config
    state.sourceLanguage = document.getElementById('source-language').value;
    state.targetLanguage = document.getElementById('target-language').value;
    state.config.includeTranslations = document.getElementById('include-translations').checked;
    state.config.useOllama = document.getElementById('use-ollama').checked;
    state.config.minFrequency = parseInt(document.getElementById('min-frequency').value);
    state.config.minWords = parseInt(document.getElementById('min-words').value);
    state.config.maxWords = parseInt(document.getElementById('max-words').value);
    state.config.excludeNumbers = document.getElementById('exclude-numbers').checked;
    
    // NUEVO: Obtener configuración de ámbito/dominio
    state.config.domainDescription = document.getElementById('domain-description').value.trim();
    state.config.useDomainClassification = document.getElementById('use-domain-classification').checked;
    
    // Go to step 3
    goToStep(3);
    
    // Start extraction process
    await extractTerms();
}

// Extract Terms
async function extractTerms() {
    try {
        updateProcessingStep(3, 'active');
        updateProgress(30, 'Extrayendo términos con TermSuite...');
        
        let extractData;
        
        if (state.fileType === 'tmx') {
            // TMX extraction - CORREGIDO: Usar POST con JSON
            const payload = {
                tmx_id: state.fileId,
                language: state.sourceLanguage,
                use_termsuite: true
            };
            
            // Incluir idioma destino siempre que esté seleccionado (necesario para que se ejecuten las traducciones)
            if (state.targetLanguage && state.targetLanguage !== state.sourceLanguage) {
                payload.target_language = state.targetLanguage;
            }
            
            // NUEVO: aplicar filtro de nº de palabras desde la extracción (para acelerar Ollama)
            if (typeof state.config.minWords === 'number') payload.min_words = state.config.minWords;
            if (typeof state.config.maxWords === 'number') payload.max_words = state.config.maxWords;

            // Incluir descripción del ámbito cuando el usuario la ha rellenado y tiene la clasificación activada
            if (state.config.useDomainClassification && state.config.domainDescription) {
                payload.domain_description = state.config.domainDescription;
            }
            
            const extractResponse = await fetch(`${API_BASE}/api/extract-tmx-language`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            
            extractData = await extractResponse.json();
            
            if (!extractResponse.ok) {
                throw new Error(extractData.detail || 'Error en la extracción');
            }
            
            // Si hay translation_job_id, monitorear progreso de traducciones y clasificación
            if (extractData.translation_job_id) {
                updateProgress(40, 'Iniciando traducciones automáticas...');
                await monitorTranslationJob(extractData.translation_job_id);
            } else if (payload.target_language) {
                // Se pidió idioma destino pero no se inició el job (p. ej. Ollama no disponible)
                showToast('Traducciones no realizadas: comprueba que Ollama esté disponible en /api/ollama/status', 'warning');
            }
        } else {
            // Corpus extraction (use min frequency 1 for corpus to get more results)
            const payload = {
                corpus_id: state.fileId,
                language: state.sourceLanguage,
                min_frequency: 1
            };
            
            const extractResponse = await fetch(`${API_BASE}/api/extract`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            
            extractData = await extractResponse.json();
            
            if (!extractResponse.ok) {
                throw new Error(extractData.detail || 'Error en la extracción');
            }
            
            // Poll for corpus job completion
            await pollCorpusJob(extractData.job_id);
            extractData = { total_terms: 0, message: 'Extracción completada' };
        }
        
        updateProcessingStep(3, 'completed');
        updateProcessingStep(4, 'active');
        updateProgress(70, 'Generando archivo Excel...');
        
        // Wait a bit for file generation
        await new Promise(resolve => setTimeout(resolve, 1500));
        
        updateProcessingStep(4, 'completed');
        updateProgress(100, '¡Completado!');
        
        // Show results
        await new Promise(resolve => setTimeout(resolve, 500));
        showResults(extractData);
        
    } catch (error) {
        showToast(`Error: ${error.message}`, 'error');
        goToStep(2);
    }
}

// Poll Corpus Job
async function pollCorpusJob(jobId) {
    return new Promise((resolve, reject) => {
        const interval = setInterval(async () => {
            try {
                const response = await fetch(`${API_BASE}/api/status/${jobId}`);
                const data = await response.json();
                
                updateProgress(30 + (data.progress * 0.4), data.message);
                
                if (data.status === 'completed') {
                    clearInterval(interval);
                    state.jobId = jobId;
                    resolve(data);
                } else if (data.status === 'failed') {
                    clearInterval(interval);
                    reject(new Error(data.error || 'Error en la extracción'));
                }
            } catch (error) {
                clearInterval(interval);
                reject(error);
            }
        }, 2000);
    });
}

// Monitor Translation Job - NUEVO
async function monitorTranslationJob(jobId) {
    return new Promise((resolve, reject) => {
        const interval = setInterval(async () => {
            try {
                const response = await fetch(`${API_BASE}/api/status/${jobId}`);
                const data = await response.json();
                
                // Progreso de 40% a 90% para traducciones
                const translationProgress = 40 + (data.progress * 0.5);
                updateProgress(translationProgress, data.message || 'Traduciendo términos...');
                
                if (data.status === 'completed') {
                    clearInterval(interval);
                    updateProgress(90, 'Traducciones completadas');
                    resolve(data);
                } else if (data.status === 'failed') {
                    clearInterval(interval);
                    console.warn('Traducciones fallaron, continuando sin ellas:', data.error);
                    // No rechazar, continuar sin traducciones
                    resolve({ status: 'completed_without_translations' });
                }
            } catch (error) {
                clearInterval(interval);
                console.warn('Error monitoreando traducciones, continuando:', error);
                // No rechazar, continuar sin traducciones
                resolve({ status: 'completed_without_translations' });
            }
        }, 2000);
    });
}

// Update Processing Step
function updateProcessingStep(stepNum, status) {
    const steps = document.querySelectorAll('.processing-step');
    const step = steps[stepNum - 1];
    
    step.classList.remove('active', 'completed');
    
    if (status === 'active') {
        step.classList.add('active');
        const icon = step.querySelector('i');
        if (icon) {
            icon.outerHTML = '<div class="spinner-border spinner-border-sm"></div>';
        }
    } else if (status === 'completed') {
        step.classList.add('completed');
        const spinner = step.querySelector('.spinner-border');
        if (spinner) {
            spinner.outerHTML = '<i class="fas fa-check-circle"></i>';
        }
    }
}

// Update Progress
function updateProgress(percent, message) {
    const progressBar = document.getElementById('extraction-progress-bar');
    const progressPercent = document.getElementById('extraction-percent');
    const statusText = document.getElementById('extraction-status');
    
    progressBar.style.width = percent + '%';
    progressPercent.textContent = percent + '%';
    statusText.textContent = message;
}

// Show Results
async function showResults(data) {
    document.getElementById('processing-view').style.display = 'none';
    document.getElementById('results-view').style.display = 'block';
    
    // Update stats
    const totalTerms = data.total_terms || 0;
    document.getElementById('stat-unique-terms').textContent = totalTerms.toLocaleString();
    
    // Get total occurrences from the terms file
    let totalOccurrences = '-';
    if (state.fileType === 'tmx' && state.fileId) {
        try {
            const termsResponse = await fetch(`${API_BASE}/api/tmx-debug/${state.fileId}`);
            if (termsResponse.ok) {
                const termsData = await termsResponse.json();
                if (termsData.details && termsData.details[state.sourceLanguage]) {
                    totalOccurrences = termsData.details[state.sourceLanguage].total_occurrences.toLocaleString();
                }
            }
        } catch (error) {
            console.error('Error getting occurrences:', error);
        }
    }
    
    document.getElementById('stat-total-occurrences').textContent = totalOccurrences;
    
    const langText = state.targetLanguage 
        ? `${state.sourceLanguage.toUpperCase()} → ${state.targetLanguage.toUpperCase()}`
        : state.sourceLanguage.toUpperCase();
    document.getElementById('stat-languages').textContent = langText;
}

// Download Results Optimized
async function downloadResultsOptimized() {
    console.log('downloadResultsOptimized clicado, state.fileId =', state.fileId);
    const downloadBtn = document.getElementById('download-btn') || document.querySelector('.btn-download');
    if (!downloadBtn || !state.fileId) {
        showToast('Error: No hay archivo cargado', 'error');
        return;
    }
    
    const originalText = downloadBtn.innerHTML;
    
    try {
        downloadBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Verificando...';
        downloadBtn.disabled = true;
        
        // Verificar si hay procesamiento unificado disponible
        const unifiedStatus = await checkUnifiedStatus(state.fileId);
        
        if (unifiedStatus.unified_ready && unifiedStatus.instant_download_available) {
            // DESCARGA INSTANTÁNEA
            downloadBtn.innerHTML = '<i class="fas fa-download"></i> Descarga instantánea...';
            
            const downloadUrl = `${API_BASE}/api/export/tmx-excel-instant/${state.fileId}`;
            
            const link = document.createElement('a');
            link.href = downloadUrl;
            link.download = `terminos_unificado_${state.sourceLanguage}_${state.targetLanguage}.xlsx`;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            
            showToast('¡Excel descargado instantáneamente con procesamiento unificado!', 'success');
            
        } else if (unifiedStatus.in_progress) {
            // MOSTRAR PROGRESO
            downloadBtn.innerHTML = `<i class="fas fa-spinner fa-spin"></i> ${unifiedStatus.progress}% - ${unifiedStatus.message}`;
            
            // Esperar y reintentar
            setTimeout(() => downloadResultsOptimized(), 2000);
            return;
            
        } else {
            // FALLBACK AL MÉTODO TRADICIONAL
            downloadBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Preparando (método tradicional)...';
            
            // Usar el método de descarga original
            await downloadResults();
        }
        
    } catch (error) {
        showToast(`Error: ${error.message}`, 'error');
    } finally {
        downloadBtn.innerHTML = originalText;
        downloadBtn.disabled = false;
    }
};

// Asegurar que esté disponible globalmente
window.downloadResultsOptimized = downloadResultsOptimized;

async function checkUnifiedStatus(tmxId) {
    try {
        const response = await fetch(`${API_BASE}/api/tmx/${tmxId}/unified-status`);
        const data = await response.json();
        return data;
    } catch (error) {
        console.error('Error checking unified status:', error);
        return { unified_ready: false };
    }
}

// Download Results (Original)
async function downloadResults() {
    const downloadBtn = document.querySelector('.btn-download');
    if (!downloadBtn) {
        console.error('Botón de descarga no encontrado');
        showToast('Error: Botón de descarga no encontrado', 'error');
        return;
    }
    
    if (!state.fileId) {
        console.error('No hay archivo cargado');
        showToast('Error: No hay archivo cargado', 'error');
        return;
    }
    
    const originalText = downloadBtn.innerHTML;
    
    if (state.fileType === 'tmx') {
        try {
            downloadBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Verificando...';
            downloadBtn.disabled = true;
            
            // NUEVO: Verificar si está listo para descarga rápida
            const readyResponse = await fetch(`${API_BASE}/api/tmx/${state.fileId}/export-ready`);
            const readyData = await readyResponse.json();
            
            if (readyData.ready_for_fast_download && state.config.includeTranslations) {
                // FLUJO RÁPIDO: Usar descarga directa con datos pre-procesados (≤100 términos)
                downloadBtn.innerHTML = '<i class="fas fa-download"></i> Descargando...';
                
                const params = {
                    min_frequency: state.config.minFrequency,
                    min_words: state.config.minWords,
                    max_words: state.config.maxWords,
                    sort_by: 'frequency',
                    format: 'excel',
                    exclude_numbers: state.config.excludeNumbers,
                    include_translation: true  // Usar datos pre-procesados
                };
                
                const queryParams = new URLSearchParams(params);
                const downloadUrl = `${API_BASE}/api/export/tmx-excel/${state.fileId}?${queryParams}`;
                
                // Descarga directa
                const link = document.createElement('a');
                link.href = downloadUrl;
                link.download = `terminos_${state.sourceLanguage}_${state.targetLanguage || 'traducido'}.xlsx`;
                document.body.appendChild(link);
                link.click();
                document.body.removeChild(link);
                
                showToast(`¡Excel descargado! (${readyData.total_terms} términos pre-procesados)`, 'success');
                
            } else {
                // FLUJO ASÍNCRONO: Usar descarga asíncrona para archivos grandes o sin pre-procesamiento
                const reason = readyData.total_terms > 100 ? 
                    `Procesando ${readyData.total_terms} términos (>100)` : 
                    readyData.needs_domain_processing ? 
                    'Clasificando términos por ámbito' :
                    'Preparando traducciones';
                downloadBtn.innerHTML = `<i class="fas fa-spinner fa-spin"></i> ${reason}...`;
                
                const params = {
                    min_frequency: state.config.minFrequency,
                    min_words: state.config.minWords,
                    max_words: state.config.maxWords,
                    sort_by: 'frequency',
                    format: 'excel',
                    exclude_numbers: state.config.excludeNumbers,
                    include_translation: state.config.includeTranslations,
                    use_ollama: state.config.useOllama
                };
                
                const queryParams = new URLSearchParams(params);
                const response = await fetch(`${API_BASE}/api/export/tmx-excel-async/${state.fileId}?${queryParams}`, {
                    method: 'POST'
                });
                
                const data = await response.json();
                
                if (response.ok) {
                    // Monitorear progreso
                    await pollExportJob(data.export_job_id);
                    showToast('Descarga completada', 'success');
                } else {
                    throw new Error(data.detail || 'Error en la exportación');
                }
            }
        } catch (error) {
            showToast(`Error: ${error.message}`, 'error');
        } finally {
            downloadBtn.innerHTML = originalText;
            downloadBtn.disabled = false;
        }
    } else {
        // Para corpus, usar descarga directa
        const downloadUrl = `${API_BASE}/api/export/excel/${state.jobId}`;
        window.location.href = downloadUrl;
        showToast('Descarga iniciada', 'success');
    }
}

// Poll Export Job
async function pollExportJob(exportJobId) {
    const downloadBtn = document.querySelector('.btn-download');
    if (!downloadBtn) {
        console.error('Botón de descarga no encontrado en pollExportJob');
        return Promise.reject(new Error('Botón de descarga no encontrado'));
    }
    
    return new Promise((resolve, reject) => {
        const interval = setInterval(async () => {
            try {
                const response = await fetch(`${API_BASE}/api/status/${exportJobId}`);
                const data = await response.json();
                
                // Actualizar botón con progreso
                downloadBtn.innerHTML = `<i class="fas fa-spinner fa-spin"></i> ${data.progress}% - ${data.message}`;
                
                if (data.status === 'completed') {
                    clearInterval(interval);
                    
                    // Descargar archivo
                    const downloadUrl = `${API_BASE}/api/download/export/${exportJobId}`;
                    window.location.href = downloadUrl;
                    
                    resolve(data);
                } else if (data.status === 'failed') {
                    clearInterval(interval);
                    reject(new Error(data.error || 'Error en la exportación'));
                }
            } catch (error) {
                clearInterval(interval);
                reject(error);
            }
        }, 1000); // Verificar cada segundo
    });
}

// Reset Wizard
function resetWizard() {
    // Guardar último análisis antes de resetear (para poder recuperarlo)
    if (state.fileId && state.fileType === 'tmx') {
        try {
            localStorage.setItem(LAST_ANALYSIS_KEY, JSON.stringify({
                fileId: state.fileId,
                fileName: state.fileName || ('tmx_' + state.fileId.slice(0, 8) + '.tmx'),
                fileType: state.fileType,
                sourceLanguage: state.sourceLanguage,
                targetLanguage: state.targetLanguage
            }));
        } catch (e) {
            console.warn('No se pudo guardar último análisis', e);
        }
    }

    state = {
        currentStep: 1,
        fileType: null,
        fileId: null,
        fileName: null,
        fileSize: null,
        availableLanguages: [],
        sourceLanguage: null,
        targetLanguage: null,
        config: {
            preset: 'standard',
            minFrequency: 2,
            minWords: 1,
            maxWords: 5,
            excludeNumbers: false,
            includeTranslations: true
        }
    };

    removeFile();
    goToStep(1);
    
    // Reset processing view
    document.getElementById('processing-view').style.display = 'block';
    document.getElementById('results-view').style.display = 'none';
    
    // Reset processing steps
    document.querySelectorAll('.processing-step').forEach((step, index) => {
        step.classList.remove('active', 'completed');
        if (index < 2) {
            step.classList.add('completed');
        }
    });
    
    // Show target language and translations options again
    document.getElementById('target-language-container').style.display = 'block';
    document.getElementById('include-translations').closest('.form-check').style.display = 'block';
}

// Mostrar/ocultar sección Recuperar último e Historial (solo en paso 1 sin archivo)
function updateRecoveryVisibility() {
    const step1 = document.getElementById('step-1');
    const filePreview = document.getElementById('file-preview');
    const recovery = document.getElementById('recovery-and-history');
    const recoverCard = document.getElementById('recover-last-card');
    if (!step1 || !recovery) return;
    const step1Active = step1.classList.contains('active');
    const noFile = !filePreview || filePreview.style.display === 'none';
    if (step1Active && noFile) {
        recovery.style.display = 'block';
        try {
            const last = localStorage.getItem(LAST_ANALYSIS_KEY);
            if (last) {
                const data = JSON.parse(last);
                recoverCard.style.display = 'block';
                document.getElementById('recover-last-info').textContent = data.fileName || ('Análisis ' + (data.fileId || '').slice(0, 8));
            } else {
                recoverCard.style.display = 'none';
            }
        } catch (e) {
            recoverCard.style.display = 'none';
        }
    } else {
        recovery.style.display = 'none';
    }
}

// Cargar historial de análisis desde la API
async function loadHistory() {
    const listEl = document.getElementById('history-list');
    const placeholder = document.getElementById('history-placeholder');
    if (!listEl || !placeholder) return;
    try {
        const response = await fetch(`${API_BASE}/api/analyses?limit=20`);
        const data = await response.json();
        placeholder.style.display = 'none';
        if (!data.analyses || data.analyses.length === 0) {
            listEl.innerHTML = '<div class="list-group-item text-muted small">No hay análisis anteriores</div>';
            return;
        }
        listEl.innerHTML = data.analyses.map(function (a) {
            const date = a.uploaded_at ? new Date(a.uploaded_at).toLocaleString('es') : '';
            const lang = a.source_language && a.target_language ? a.source_language + ' → ' + a.target_language : (a.source_language || '');
            const name = (a.original_filename || a.tmx_id || '').replace(/"/g, '&quot;');
            const tmxIdEsc = JSON.stringify(a.tmx_id);
            return '<div class="list-group-item d-flex justify-content-between align-items-start flex-wrap gap-2">' +
                '<div class="flex-grow-1 min-w-0">' +
                '<button type="button" class="btn btn-link btn-sm p-0 text-start text-decoration-none text-dark w-100" onclick="restoreFromHistory(' + tmxIdEsc + ')">' +
                '<div class="d-flex justify-content-between align-items-center"><span class="text-truncate me-2" title="' + name + '">' + name + '</span><span class="badge bg-secondary">' + (a.total_terms || 0) + ' términos</span></div>' +
                '<div class="small text-muted mt-1">' + date + (lang ? ' · ' + lang : '') + '</div>' +
                '</button>' +
                '</div>' +
                '<a href="#" class="btn btn-success btn-sm flex-shrink-0" onclick="event.preventDefault(); downloadAnalysisExcel(' + tmxIdEsc + ');" title="Descargar Excel">' +
                '<i class="fas fa-file-excel me-1"></i>Descargar Excel</a>' +
                '</div>';
        }).join('');
    } catch (e) {
        placeholder.textContent = 'No se pudo cargar el historial';
    }
}

// Recuperar último análisis (ir a paso 3 con el mismo fileId)
async function restoreLastAnalysis() {
    try {
        const last = localStorage.getItem(LAST_ANALYSIS_KEY);
        if (!last) return;
        const data = JSON.parse(last);
        if (!data.fileId) return;
        await restoreAnalysisState(data.fileId, data.fileName, data.sourceLanguage, data.targetLanguage);
    } catch (e) {
        showToast('Error al recuperar el análisis', 'error');
    }
}

// Restaurar un análisis del historial
async function restoreFromHistory(tmxId) {
    if (!tmxId) return;
    try {
        const response = await fetch(`${API_BASE}/api/analyses/${tmxId}/summary`);
        if (!response.ok) throw new Error('Análisis no encontrado');
        const summary = await response.json();
        await restoreAnalysisState(
            summary.tmx_id,
            summary.original_filename,
            summary.source_language,
            summary.target_language,
            { total_terms: summary.total_terms, total_occurrences: summary.total_occurrences }
        );
    } catch (e) {
        showToast('Error al abrir el análisis: ' + (e.message || ''), 'error');
    }
}

// Descargar Excel de un análisis del historial (sin abrir la vista de resultados)
async function downloadAnalysisExcel(tmxId) {
    if (!tmxId) return;
    try {
        const response = await fetch(`${API_BASE}/api/analyses/${tmxId}/summary`);
        if (!response.ok) throw new Error('Análisis no encontrado');
        const summary = await response.json();
        state.fileId = summary.tmx_id;
        state.fileName = summary.original_filename || ('tmx_' + summary.tmx_id.slice(0, 8) + '.tmx');
        state.fileType = 'tmx';
        state.sourceLanguage = summary.source_language || '';
        state.targetLanguage = summary.target_language || '';
        if (typeof state.config === 'undefined') state.config = {};
        state.config.includeTranslations = state.config.includeTranslations !== false;
        await downloadResultsOptimized();
    } catch (e) {
        showToast('Error al descargar: ' + (e.message || ''), 'error');
    }
}

// Restaurar estado y mostrar vista de resultados (paso 3)
async function restoreAnalysisState(fileId, fileName, sourceLanguage, targetLanguage, stats) {
    state.fileId = fileId;
    state.fileName = fileName || ('tmx_' + fileId.slice(0, 8) + '.tmx');
    state.fileType = 'tmx';
    state.sourceLanguage = sourceLanguage || '';
    state.targetLanguage = targetLanguage || '';
    state.currentStep = 3;
    goToStep(3);
    document.getElementById('processing-view').style.display = 'none';
    document.getElementById('results-view').style.display = 'block';
    if (stats) {
        document.getElementById('stat-unique-terms').textContent = (stats.total_terms || 0).toLocaleString();
        document.getElementById('stat-total-occurrences').textContent = (stats.total_occurrences != null ? stats.total_occurrences : '-').toLocaleString();
    } else {
        try {
            const res = await fetch(`${API_BASE}/api/analyses/${fileId}/summary`);
            if (res.ok) {
                const s = await res.json();
                document.getElementById('stat-unique-terms').textContent = (s.total_terms || 0).toLocaleString();
                document.getElementById('stat-total-occurrences').textContent = (s.total_occurrences != null ? s.total_occurrences : '-').toLocaleString();
            }
        } catch (e) {
            document.getElementById('stat-unique-terms').textContent = '0';
            document.getElementById('stat-total-occurrences').textContent = '-';
        }
    }
    const langText = (state.targetLanguage ? state.sourceLanguage + ' → ' + state.targetLanguage : state.sourceLanguage || '-').toUpperCase();
    document.getElementById('stat-languages').textContent = langText;
    updateRecoveryVisibility();
}

// Show Toast
function showToast(message, type = 'info') {
    const colors = {
        success: '#10b981',
        error: '#ef4444',
        warning: '#f59e0b',
        info: '#4f46e5'
    };
    
    const toast = document.createElement('div');
    toast.style.cssText = `
        position: fixed;
        bottom: 2rem;
        right: 2rem;
        background: ${colors[type]};
        color: white;
        padding: 1rem 1.5rem;
        border-radius: 0.5rem;
        box-shadow: 0 4px 6px rgba(0,0,0,0.2);
        z-index: 9999;
        animation: slideIn 0.3s;
    `;
    toast.textContent = message;
    
    document.body.appendChild(toast);
    
    setTimeout(() => {
        toast.style.animation = 'slideOut 0.3s';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// Format File Size
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
}

// Add animations
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from { transform: translateX(100%); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }
    @keyframes slideOut {
        from { transform: translateX(0); opacity: 1; }
        to { transform: translateX(100%); opacity: 0; }
    }
`;
document.head.appendChild(style);

// Check Ollama Status
async function checkOllamaStatus() {
    try {
        const response = await fetch(`${API_BASE}/api/ollama/status`);
        const data = await response.json();
        
        const ollamaCheckbox = document.getElementById('use-ollama');
        const ollamaLabel = ollamaCheckbox.nextElementSibling;
        
        if (data.available) {
            // Ollama disponible
            ollamaCheckbox.disabled = false;
            ollamaLabel.classList.remove('text-muted');
            
            // Actualizar texto con información del modelo
            const modelInfo = data.model ? ` (${data.model})` : '';
            ollamaLabel.innerHTML = `
                <i class="fas fa-robot me-1 text-success"></i>Usar Ollama para términos sin traducción${modelInfo}
                <small class="d-block text-muted">Traduce automáticamente términos con coincidencia parcial</small>
            `;
        } else {
            // Ollama no disponible
            ollamaCheckbox.disabled = true;
            ollamaCheckbox.checked = false;
            state.config.useOllama = false;
            ollamaLabel.classList.add('text-muted');
            
            ollamaLabel.innerHTML = `
                <i class="fas fa-robot me-1 text-danger"></i>Ollama no disponible
                <small class="d-block text-muted">Servidor Ollama no encontrado: ${data.error || 'dirección configurada'}</small>
            `;
        }
    } catch (error) {
        console.error('Error checking Ollama status:', error);
        
        // En caso de error, deshabilitar Ollama
        const ollamaCheckbox = document.getElementById('use-ollama');
        const ollamaLabel = ollamaCheckbox.nextElementSibling;
        
        ollamaCheckbox.disabled = true;
        ollamaCheckbox.checked = false;
        state.config.useOllama = false;
        ollamaLabel.classList.add('text-muted');
        
        ollamaLabel.innerHTML = `
            <i class="fas fa-robot me-1 text-warning"></i>Ollama no disponible
            <small class="d-block text-muted">No se pudo verificar el estado del servidor</small>
        `;
    }
}