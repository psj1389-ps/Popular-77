/**
 * GIF Converter for Image to GIF Converter
 * Handles image processing and GIF generation using gif.js library
 */

class GifConverter {
    constructor() {
        this.gif = null;
        this.isConverting = false;
        this.conversionSettings = {
            width: 500,
            height: 500,
            quality: 10,
            delay: 500,
            repeat: 0, // 0 = infinite loop
            workers: 2,
            workerScript: './lib/gif.worker.js',
            dither: false,
            transparent: null,
            background: '#ffffff'
        };
        
        this.initializeElements();
        this.setupEventListeners();
    }
    
    initializeElements() {
        this.convertBtn = document.getElementById('convert-btn');
        this.conversionProgress = document.getElementById('conversion-progress');
        this.progressContainer = document.getElementById('progress-container');
        this.progressBar = document.getElementById('progress-fill');
        this.progressText = document.getElementById('progress-text');
        this.progressPercent = document.getElementById('progress-percent');
        this.resultsSection = document.getElementById('results-section');
        this.resultsList = document.getElementById('results-grid');
        this.downloadAllBtn = document.getElementById('download-all-btn');
        
        // Settings elements
        this.widthInput = document.getElementById('width-input');
        this.heightInput = document.getElementById('height-input');
        this.qualityInput = document.getElementById('quality-input');
        this.delayInput = document.getElementById('delay-input');
        this.repeatInput = document.getElementById('repeat-input');
        this.maintainAspectRatio = document.getElementById('maintain-aspect-ratio');
        
        // Load saved settings
        this.loadSettings();
    }
    
    setupEventListeners() {
        // Convert button
        this.convertBtn.addEventListener('click', this.startConversion.bind(this));
        
        // Settings change listeners
        this.widthInput.addEventListener('change', this.updateSettings.bind(this));
        this.heightInput.addEventListener('change', this.updateSettings.bind(this));
        this.qualityInput.addEventListener('change', this.updateSettings.bind(this));
        this.delayInput.addEventListener('change', this.updateSettings.bind(this));
        this.repeatInput.addEventListener('change', this.updateSettings.bind(this));
        this.maintainAspectRatio.addEventListener('change', this.updateSettings.bind(this));
        
        // Aspect ratio maintenance
        this.widthInput.addEventListener('input', this.handleAspectRatio.bind(this));
        this.heightInput.addEventListener('input', this.handleAspectRatio.bind(this));
        
        // Download all button
        this.downloadAllBtn.addEventListener('click', this.downloadAllResults.bind(this));
        
        // Listen for file updates
        document.addEventListener('filesUpdated', this.handleFilesUpdated.bind(this));
    }
    
    handleFilesUpdated(event) {
        const { files } = event.detail;
        
        // Enable/disable convert button
        this.convertBtn.disabled = files.length === 0 || this.isConverting;
        
        // Update convert button text
        if (files.length === 0) {
            this.convertBtn.textContent = 'Select Images to Convert';
        } else {
            this.convertBtn.textContent = `Convert ${files.length} Image${files.length > 1 ? 's' : ''} to GIF`;
        }
    }
    
    updateSettings() {
        this.conversionSettings.width = parseInt(this.widthInput.value) || 500;
        this.conversionSettings.height = parseInt(this.heightInput.value) || 500;
        this.conversionSettings.quality = parseInt(this.qualityInput.value) || 10;
        this.conversionSettings.delay = parseInt(this.delayInput.value) || 500;
        this.conversionSettings.repeat = parseInt(this.repeatInput.value) || 0;
        
        // Save settings
        Utils.StorageUtils.saveSettings(this.conversionSettings);
        
        // Update quality display
        const qualityDisplay = document.getElementById('quality-display');
        if (qualityDisplay) {
            qualityDisplay.textContent = this.conversionSettings.quality;
        }
        
        // Update delay display
        const delayDisplay = document.getElementById('delay-display');
        if (delayDisplay) {
            delayDisplay.textContent = `${this.conversionSettings.delay}ms`;
        }
    }
    
    handleAspectRatio(event) {
        if (!this.maintainAspectRatio.checked) return;
        
        const isWidthChange = event.target === this.widthInput;
        const newValue = parseInt(event.target.value);
        
        if (!newValue || newValue <= 0) return;
        
        // Calculate aspect ratio based on first image if available
        const files = window.FileHandler ? window.FileHandler.getFiles() : [];
        if (files.length === 0) return;
        
        // Use first image for aspect ratio calculation
        const firstFile = files[0];
        this.calculateAspectRatio(firstFile.file, newValue, isWidthChange);
    }
    
    async calculateAspectRatio(file, newValue, isWidthChange) {
        try {
            const img = await this.loadImage(file);
            const aspectRatio = img.width / img.height;
            
            if (isWidthChange) {
                const newHeight = Math.round(newValue / aspectRatio);
                this.heightInput.value = newHeight;
            } else {
                const newWidth = Math.round(newValue * aspectRatio);
                this.widthInput.value = newWidth;
            }
            
            this.updateSettings();
        } catch (error) {
            console.warn('Failed to calculate aspect ratio:', error);
        }
    }
    
    loadSettings() {
        const savedSettings = Utils.StorageUtils.loadSettings();
        if (savedSettings) {
            this.conversionSettings = { ...this.conversionSettings, ...savedSettings };
            
            // Update UI elements
            this.widthInput.value = this.conversionSettings.width;
            this.heightInput.value = this.conversionSettings.height;
            this.qualityInput.value = this.conversionSettings.quality;
            this.delayInput.value = this.conversionSettings.delay;
            this.repeatInput.value = this.conversionSettings.repeat;
        }
    }
    
    async startConversion() {
        if (this.isConverting) return;
        
        const files = window.FileHandler ? window.FileHandler.getFiles() : [];
        if (files.length === 0) {
            Utils.ErrorHandler.showError('No files selected for conversion.');
            return;
        }
        
        // Validate files
        const validation = window.FileHandler.validateFiles();
        if (!validation.isValid) {
            Utils.ErrorHandler.showError(validation.errors.join(' '));
            return;
        }
        
        this.isConverting = true;
        this.updateConversionUI(true);
        
        Utils.PerformanceMonitor.start('totalConversion');
        
        try {
            // Clear previous results
            this.clearResults();
            
            // Convert each file
            for (let i = 0; i < files.length; i++) {
                const file = files[i];
                
                // Update overall progress
                const overallProgress = i / files.length;
                this.updateProgress(overallProgress, `Converting ${i + 1} of ${files.length}...`);
                
                // Update file status
                window.FileHandler.updateFileStatus(file.id, 'processing', 0);
                
                try {
                    const result = await this.convertSingleImage(file, (progress) => {
                        window.FileHandler.updateFileStatus(file.id, 'processing', progress);
                    });
                    
                    // Mark file as completed
                    window.FileHandler.updateFileStatus(file.id, 'completed', 1);
                    
                    // Add result to UI
                    this.addResult(result);
                    
                } catch (error) {
                    Utils.ErrorHandler.logError(error, `convertSingleImage: ${file.name}`);
                    window.FileHandler.updateFileStatus(file.id, 'error');
                    Utils.ErrorHandler.showError(`Failed to convert "${file.name}": ${error.message}`);
                }
            }
            
            // Final progress update
            this.updateProgress(1, 'Conversion completed!');
            
            // Show results section
            this.showResults();
            
            Utils.ErrorHandler.showSuccess(`Successfully converted ${files.length} image${files.length > 1 ? 's' : ''} to GIF!`);
            
        } catch (error) {
            Utils.ErrorHandler.logError(error, 'startConversion');
            Utils.ErrorHandler.showError('Conversion failed. Please try again.');
        } finally {
            this.isConverting = false;
            this.updateConversionUI(false);
            Utils.PerformanceMonitor.end('totalConversion');
        }
    }
    
    async convertSingleImage(fileObj, progressCallback) {
        return new Promise(async (resolve, reject) => {
            try {
                Utils.PerformanceMonitor.start(`convert_${fileObj.id}`);
                
                // Load image
                const img = await this.loadImage(fileObj.file);
                
                // Create GIF instance
                const gif = new GIF({
                    workers: this.conversionSettings.workers,
                    quality: this.conversionSettings.quality,
                    width: this.conversionSettings.width,
                    height: this.conversionSettings.height,
                    workerScript: this.conversionSettings.workerScript,
                    dither: this.conversionSettings.dither,
                    transparent: this.conversionSettings.transparent,
                    background: this.conversionSettings.background,
                    repeat: this.conversionSettings.repeat
                });
                
                // Progress tracking
                gif.on('progress', (progress) => {
                    if (progressCallback) {
                        progressCallback(progress);
                    }
                });
                
                // Handle completion
                gif.on('finished', (blob) => {
                    const duration = Utils.PerformanceMonitor.end(`convert_${fileObj.id}`);
                    
                    const result = {
                        id: `result_${fileObj.id}`,
                        originalFile: fileObj,
                        blob: blob,
                        url: URL.createObjectURL(blob),
                        filename: this.generateGifFilename(fileObj.name),
                        size: blob.size,
                        conversionTime: duration,
                        settings: { ...this.conversionSettings }
                    };
                    
                    resolve(result);
                });
                
                // Handle errors
                gif.on('error', (error) => {
                    Utils.PerformanceMonitor.end(`convert_${fileObj.id}`);
                    reject(new Error(`GIF generation failed: ${error.message}`));
                });
                
                // Resize and add image to GIF
                const canvas = await this.resizeImage(img, this.conversionSettings.width, this.conversionSettings.height);
                gif.addFrame(canvas, { delay: this.conversionSettings.delay });
                
                // Start rendering
                gif.render();
                
            } catch (error) {
                Utils.PerformanceMonitor.end(`convert_${fileObj.id}`);
                reject(error);
            }
        });
    }
    
    async loadImage(file) {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            
            reader.onload = function(e) {
                const img = new Image();
                
                img.onload = function() {
                    resolve(img);
                };
                
                img.onerror = function() {
                    reject(new Error('Failed to load image'));
                };
                
                img.src = e.target.result;
            };
            
            reader.onerror = function() {
                reject(new Error('Failed to read file'));
            };
            
            reader.readAsDataURL(file);
        });
    }
    
    async resizeImage(img, targetWidth, targetHeight) {
        const canvas = document.createElement('canvas');
        const ctx = canvas.getContext('2d');
        
        canvas.width = targetWidth;
        canvas.height = targetHeight;
        
        // Calculate scaling to maintain aspect ratio
        const scale = Math.min(targetWidth / img.width, targetHeight / img.height);
        const scaledWidth = img.width * scale;
        const scaledHeight = img.height * scale;
        
        // Center the image
        const x = (targetWidth - scaledWidth) / 2;
        const y = (targetHeight - scaledHeight) / 2;
        
        // Fill background
        ctx.fillStyle = this.conversionSettings.background;
        ctx.fillRect(0, 0, targetWidth, targetHeight);
        
        // Draw image
        ctx.drawImage(img, x, y, scaledWidth, scaledHeight);
        
        return canvas;
    }
    
    generateGifFilename(originalName) {
        const nameWithoutExt = originalName.substring(0, originalName.lastIndexOf('.'));
        return `${nameWithoutExt}.gif`;
    }
    
    updateConversionUI(isConverting) {
        this.convertBtn.disabled = isConverting;
        this.convertBtn.textContent = isConverting ? 'Converting...' : 'Convert to GIF';
        
        if (isConverting) {
            this.conversionProgress.style.display = 'block';
            Utils.AnimationUtils.fadeIn(this.conversionProgress, 300);
        } else {
            setTimeout(() => {
                this.conversionProgress.style.display = 'none';
            }, 1000);
        }
    }
    
    updateProgress(progress, message) {
        const percentage = Math.round(progress * 100);
        
        if (this.progressBar) {
            this.progressBar.style.width = `${percentage}%`;
        }
        
        if (this.progressText) {
            this.progressText.textContent = message || `${percentage}%`;
        }
    }
    
    clearResults() {
        this.resultsList.innerHTML = '';
        this.resultsSection.style.display = 'none';
    }
    
    addResult(result) {
        const resultCard = document.createElement('div');
        resultCard.className = 'result-card';
        resultCard.dataset.resultId = result.id;
        
        resultCard.innerHTML = `
            <div class="result-preview">
                <img src="${result.url}" alt="${result.filename}" loading="lazy">
            </div>
            <div class="result-info">
                <div class="result-filename" title="${result.filename}">${result.filename}</div>
                <div class="result-details">
                    <span class="result-size">${Utils.formatFileSize(result.size)}</span>
                    <span class="conversion-time">${result.conversionTime ? Math.round(result.conversionTime) + 'ms' : ''}</span>
                </div>
                <div class="result-settings">
                    <span>${result.settings.width}×${result.settings.height}</span>
                    <span>Quality: ${result.settings.quality}</span>
                    <span>Delay: ${result.settings.delay}ms</span>
                </div>
            </div>
            <div class="result-actions">
                <button class="download-btn" data-result-id="${result.id}" title="Download GIF">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
                        <polyline points="7,10 12,15 17,10"></polyline>
                        <line x1="12" y1="15" x2="12" y2="3"></line>
                    </svg>
                    Download
                </button>
                <button class="preview-btn" data-result-id="${result.id}" title="Preview in new tab">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path>
                        <circle cx="12" cy="12" r="3"></circle>
                    </svg>
                    Preview
                </button>
            </div>
        `;
        
        // Add event listeners
        const downloadBtn = resultCard.querySelector('.download-btn');
        const previewBtn = resultCard.querySelector('.preview-btn');
        
        downloadBtn.addEventListener('click', () => this.downloadResult(result.id));
        previewBtn.addEventListener('click', () => this.previewResult(result.id));
        
        // Add to results list
        this.resultsList.appendChild(resultCard);
        
        // Animate in
        Utils.AnimationUtils.fadeIn(resultCard, 300);
        
        // Store result for later access
        if (!this.results) {
            this.results = [];
        }
        this.results.push(result);
    }
    
    showResults() {
        this.resultsSection.style.display = 'block';
        Utils.AnimationUtils.fadeIn(this.resultsSection, 300);
        
        // Scroll to results
        this.resultsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
    
    downloadResult(resultId) {
        const result = this.results.find(r => r.id === resultId);
        if (!result) return;
        
        Utils.downloadFile(result.blob, result.filename);
        Utils.ErrorHandler.showSuccess(`"${result.filename}" downloaded successfully!`);
    }
    
    previewResult(resultId) {
        const result = this.results.find(r => r.id === resultId);
        if (!result) return;
        
        // Open in new tab
        const newWindow = window.open();
        newWindow.document.write(`
            <!DOCTYPE html>
            <html>
            <head>
                <title>GIF Preview - ${result.filename}</title>
                <style>
                    body { 
                        margin: 0; 
                        padding: 20px; 
                        background: #f0f0f0; 
                        display: flex; 
                        justify-content: center; 
                        align-items: center; 
                        min-height: 100vh; 
                        font-family: Arial, sans-serif;
                    }
                    .preview-container {
                        background: white;
                        padding: 20px;
                        border-radius: 8px;
                        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
                        text-align: center;
                    }
                    img { 
                        max-width: 100%; 
                        height: auto; 
                        border-radius: 4px;
                    }
                    .info {
                        margin-top: 15px;
                        color: #666;
                        font-size: 14px;
                    }
                </style>
            </head>
            <body>
                <div class="preview-container">
                    <h2>${result.filename}</h2>
                    <img src="${result.url}" alt="${result.filename}">
                    <div class="info">
                        <p>Size: ${Utils.formatFileSize(result.size)}</p>
                        <p>Dimensions: ${result.settings.width}×${result.settings.height}</p>
                        <p>Quality: ${result.settings.quality}</p>
                    </div>
                </div>
            </body>
            </html>
        `);
    }
    
    async downloadAllResults() {
        if (!this.results || this.results.length === 0) {
            Utils.ErrorHandler.showError('No results to download.');
            return;
        }
        
        try {
            // For single file, download directly
            if (this.results.length === 1) {
                this.downloadResult(this.results[0].id);
                return;
            }
            
            // For multiple files, create a simple download sequence
            Utils.ErrorHandler.showSuccess(`Downloading ${this.results.length} files...`);
            
            for (const result of this.results) {
                await new Promise(resolve => {
                    Utils.downloadFile(result.blob, result.filename);
                    setTimeout(resolve, 500); // Small delay between downloads
                });
            }
            
            Utils.ErrorHandler.showSuccess('All files downloaded successfully!');
            
        } catch (error) {
            Utils.ErrorHandler.logError(error, 'downloadAllResults');
            Utils.ErrorHandler.showError('Failed to download all files. Please try downloading individually.');
        }
    }
    
    // Public methods
    getResults() {
        return this.results || [];
    }
    
    getSettings() {
        return { ...this.conversionSettings };
    }
    
    updateSetting(key, value) {
        if (key in this.conversionSettings) {
            this.conversionSettings[key] = value;
            Utils.StorageUtils.saveSettings(this.conversionSettings);
        }
    }
}

// Initialize GIF converter when DOM is loaded
let gifConverter;

document.addEventListener('DOMContentLoaded', () => {
    gifConverter = new GifConverter();
    
    // Make it globally accessible
    window.GifConverter = gifConverter;
});

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = GifConverter;
}