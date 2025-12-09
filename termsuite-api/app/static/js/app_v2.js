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
        includeTranslations: true
    }
};

const API_BASE = '';

// Inicialización
document.addEventListener('DOMContentLoaded', function() {
    setupFileUpload();
    setupDragAndDrop();
});

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
    
    // Set default selection
    if (languages.length >= 2) {
        sourceSelect.value = languages[0];
        targetSelect.value = languages[1];
        state.sourceLanguage = languages[0];
        state.targetLanguage = languages[1];
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
    state.tmxId = null;
    state.fileName = null;
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
    state.config.minFrequency = parseInt(document.getElementById('min-frequency').value);
    state.config.minWords = parseInt(document.getElementById('min-words').value);
    state.config.maxWords = parseInt(document.getElementById('max-words').value);
    state.config.excludeNumbers = document.getElementById('exclude-numbers').checked;
    
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
            // TMX extraction
            let url = `${API_BASE}/api/extract-tmx-language?tmx_id=${state.fileId}&language=${state.sourceLanguage}`;
            
            if (state.targetLanguage && state.availableLanguages.length > 1) {
                url += `&target_language=${state.targetLanguage}`;
            }
            
            url += `&use_termsuite=true`;
            
            const extractResponse = await fetch(url, { method: 'POST' });
            extractData = await extractResponse.json();
            
            if (!extractResponse.ok) {
                throw new Error(extractData.detail || 'Error en la extracción');
            }
        } else {
            // Corpus extraction
            const payload = {
                corpus_id: state.fileId,
                language: state.sourceLanguage,
                min_frequency: state.config.minFrequency
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

// Download Results
function downloadResults() {
    let downloadUrl;
    
    if (state.fileType === 'tmx') {
        const params = new URLSearchParams({
            min_frequency: state.config.minFrequency,
            min_words: state.config.minWords,
            max_words: state.config.maxWords,
            sort_by: 'frequency',
            format: 'excel',
            exclude_numbers: state.config.excludeNumbers,
            include_translation: state.config.includeTranslations
        });
        downloadUrl = `${API_BASE}/api/export/tmx-excel/${state.fileId}?${params.toString()}`;
    } else {
        downloadUrl = `${API_BASE}/api/export/excel/${state.jobId}`;
    }
    
    window.location.href = downloadUrl;
    showToast('Descarga iniciada', 'success');
}

// Reset Wizard
function resetWizard() {
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
