/**
 * File Handler for Image to GIF Converter
 * Handles file upload, drag & drop, validation, and preview generation
 */

class FileHandler {
    constructor() {
        this.files = [];
        this.maxFiles = 100;
        this.maxTotalSize = 500 * 1024 * 1024; // 500MB
        this.currentTotalSize = 0;
        
        this.initializeElements();
        this.setupEventListeners();
    }
    
    initializeElements() {
        this.uploadArea = document.getElementById('upload-area');
        this.fileInput = document.getElementById('file-input');
        this.browseBtn = document.getElementById('browse-btn');
        this.fileList = document.getElementById('file-list');
        this.fileCount = document.getElementById('file-count');
        this.totalSize = document.getElementById('total-size');
        this.clearAllBtn = document.getElementById('clear-all-btn');
        this.previewSection = document.getElementById('preview-section');
    }
    
    setupEventListeners() {
        // Drag and drop events
        this.uploadArea.addEventListener('dragover', this.handleDragOver.bind(this));
        this.uploadArea.addEventListener('dragleave', this.handleDragLeave.bind(this));
        this.uploadArea.addEventListener('drop', this.handleDrop.bind(this));
        
        // File input events
        this.fileInput.addEventListener('change', this.handleFileSelect.bind(this));
        this.browseBtn.addEventListener('click', () => this.fileInput.click());
        
        // Clear all files
        this.clearAllBtn.addEventListener('click', this.clearAllFiles.bind(this));
        
        // Prevent default drag behaviors on document
        document.addEventListener('dragover', (e) => e.preventDefault());
        document.addEventListener('drop', (e) => e.preventDefault());
    }
    
    handleDragOver(e) {
        e.preventDefault();
        this.uploadArea.classList.add('drag-over');
    }
    
    handleDragLeave(e) {
        e.preventDefault();
        // Only remove drag-over class if we're leaving the upload area entirely
        if (!this.uploadArea.contains(e.relatedTarget)) {
            this.uploadArea.classList.remove('drag-over');
        }
    }
    
    handleDrop(e) {
        e.preventDefault();
        this.uploadArea.classList.remove('drag-over');
        
        const files = Array.from(e.dataTransfer.files);
        this.processFiles(files);
    }
    
    handleFileSelect(e) {
        const files = Array.from(e.target.files);
        this.processFiles(files);
        
        // Reset file input
        e.target.value = '';
    }
    
    async processFiles(newFiles) {
        Utils.PerformanceMonitor.start('processFiles');
        
        try {
            // Filter valid image files
            const validFiles = newFiles.filter(file => {
                if (!Utils.isValidImageFile(file)) {
                    Utils.ErrorHandler.showError(`"${file.name}" is not a supported image format.`);
                    return false;
                }
                return true;
            });
            
            if (validFiles.length === 0) {
                return;
            }
            
            // Check file count limit
            if (this.files.length + validFiles.length > this.maxFiles) {
                Utils.ErrorHandler.showError(`Maximum ${this.maxFiles} files allowed. You can add ${this.maxFiles - this.files.length} more files.`);
                return;
            }
            
            // Check total size limit
            const newTotalSize = validFiles.reduce((sum, file) => sum + file.size, 0);
            if (this.currentTotalSize + newTotalSize > this.maxTotalSize) {
                const remainingSize = this.maxTotalSize - this.currentTotalSize;
                Utils.ErrorHandler.showError(`Total file size limit (500MB) exceeded. You have ${Utils.formatFileSize(remainingSize)} remaining.`);
                return;
            }
            
            // Process each file
            for (const file of validFiles) {
                await this.addFile(file);
            }
            
            this.updateUI();
            Utils.ErrorHandler.showSuccess(`${validFiles.length} file(s) added successfully!`);
            
        } catch (error) {
            Utils.ErrorHandler.logError(error, 'processFiles');
            Utils.ErrorHandler.showError('Failed to process files. Please try again.');
        } finally {
            Utils.PerformanceMonitor.end('processFiles');
        }
    }
    
    async addFile(file) {
        try {
            // Generate unique ID for the file
            const fileId = `file_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
            
            // Create file object
            const fileObj = {
                id: fileId,
                file: file,
                name: file.name,
                size: file.size,
                type: file.type,
                lastModified: file.lastModified,
                thumbnail: null,
                status: 'pending' // pending, processing, completed, error
            };
            
            // Generate thumbnail
            try {
                fileObj.thumbnail = await Utils.createThumbnail(file);
            } catch (error) {
                console.warn('Failed to generate thumbnail for', file.name, error);
                fileObj.thumbnail = this.getDefaultThumbnail(file.type);
            }
            
            // Add to files array
            this.files.push(fileObj);
            this.currentTotalSize += file.size;
            
            // Create file card in UI
            this.createFileCard(fileObj);
            
        } catch (error) {
            Utils.ErrorHandler.logError(error, 'addFile');
            throw error;
        }
    }
    
    createFileCard(fileObj) {
        const fileCard = document.createElement('div');
        fileCard.className = 'file-card';
        fileCard.dataset.fileId = fileObj.id;
        
        fileCard.innerHTML = `
            <div class="file-thumbnail">
                <img src="${fileObj.thumbnail}" alt="${fileObj.name}" loading="lazy">
            </div>
            <div class="file-info">
                <div class="file-name" title="${fileObj.name}">${fileObj.name}</div>
                <div class="file-details">
                    <span class="file-size">${Utils.formatFileSize(fileObj.size)}</span>
                    <span class="file-type">${Utils.getFileExtension(fileObj.name).toUpperCase()}</span>
                </div>
                <div class="file-status">
                    <span class="status-text">Ready</span>
                    <div class="file-progress" style="display: none;">
                        <div class="progress-bar">
                            <div class="progress-fill" style="width: 0%"></div>
                        </div>
                        <span class="progress-text">0%</span>
                    </div>
                </div>
            </div>
            <button class="remove-file-btn" title="Remove file" data-file-id="${fileObj.id}">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <line x1="18" y1="6" x2="6" y2="18"></line>
                    <line x1="6" y1="6" x2="18" y2="18"></line>
                </svg>
            </button>
        `;
        
        // Add remove event listener
        const removeBtn = fileCard.querySelector('.remove-file-btn');
        removeBtn.addEventListener('click', () => this.removeFile(fileObj.id));
        
        // Add file card to list
        this.fileList.appendChild(fileCard);
        
        // Animate in
        Utils.AnimationUtils.fadeIn(fileCard, 200);
    }
    
    removeFile(fileId) {
        const fileIndex = this.files.findIndex(f => f.id === fileId);
        if (fileIndex === -1) return;
        
        const file = this.files[fileIndex];
        
        // Remove from array
        this.files.splice(fileIndex, 1);
        this.currentTotalSize -= file.file.size;
        
        // Remove from UI
        const fileCard = document.querySelector(`[data-file-id="${fileId}"]`);
        if (fileCard) {
            Utils.AnimationUtils.fadeOut(fileCard, 200);
            setTimeout(() => {
                if (fileCard.parentNode) {
                    fileCard.parentNode.removeChild(fileCard);
                }
            }, 200);
        }
        
        this.updateUI();
        
        // Show feedback
        Utils.ErrorHandler.showSuccess(`"${file.name}" removed successfully.`);
    }
    
    clearAllFiles() {
        if (this.files.length === 0) return;
        
        const fileCount = this.files.length;
        
        // Clear arrays
        this.files = [];
        this.currentTotalSize = 0;
        
        // Clear UI
        this.fileList.innerHTML = '';
        
        this.updateUI();
        
        Utils.ErrorHandler.showSuccess(`${fileCount} file(s) cleared successfully.`);
    }
    
    updateUI() {
        // Update file count
        this.fileCount.textContent = this.files.length;
        
        // Update total size
        this.totalSize.textContent = Utils.formatFileSize(this.currentTotalSize);
        
        // Show/hide preview section
        if (this.files.length > 0) {
            this.previewSection.style.display = 'block';
            Utils.AnimationUtils.fadeIn(this.previewSection, 300);
        } else {
            this.previewSection.style.display = 'none';
        }
        
        // Update upload area state
        if (this.files.length > 0) {
            this.uploadArea.classList.add('has-files');
        } else {
            this.uploadArea.classList.remove('has-files');
        }
        
        // Enable/disable clear button
        this.clearAllBtn.disabled = this.files.length === 0;
        
        // Update file limit indicators
        this.updateLimitIndicators();
        
        // Trigger custom event for other components
        document.dispatchEvent(new CustomEvent('filesUpdated', {
            detail: {
                files: this.files,
                count: this.files.length,
                totalSize: this.currentTotalSize
            }
        }));
    }
    
    updateLimitIndicators() {
        // Update file count indicator
        const fileCountIndicator = document.querySelector('.file-count-indicator');
        if (fileCountIndicator) {
            const percentage = (this.files.length / this.maxFiles) * 100;
            fileCountIndicator.style.width = `${percentage}%`;
            
            if (percentage > 80) {
                fileCountIndicator.classList.add('warning');
            } else {
                fileCountIndicator.classList.remove('warning');
            }
        }
        
        // Update size indicator
        const sizeIndicator = document.querySelector('.size-indicator');
        if (sizeIndicator) {
            const percentage = (this.currentTotalSize / this.maxTotalSize) * 100;
            sizeIndicator.style.width = `${percentage}%`;
            
            if (percentage > 80) {
                sizeIndicator.classList.add('warning');
            } else {
                sizeIndicator.classList.remove('warning');
            }
        }
    }
    
    updateFileStatus(fileId, status, progress = null) {
        const fileCard = document.querySelector(`[data-file-id="${fileId}"]`);
        if (!fileCard) return;
        
        const statusText = fileCard.querySelector('.status-text');
        const progressContainer = fileCard.querySelector('.file-progress');
        const progressFill = fileCard.querySelector('.progress-fill');
        const progressText = fileCard.querySelector('.progress-text');
        
        // Update file object
        const file = this.files.find(f => f.id === fileId);
        if (file) {
            file.status = status;
        }
        
        // Update UI based on status
        switch (status) {
            case 'processing':
                statusText.textContent = 'Processing...';
                progressContainer.style.display = 'block';
                fileCard.classList.add('processing');
                break;
                
            case 'completed':
                statusText.textContent = 'Completed';
                progressContainer.style.display = 'none';
                fileCard.classList.remove('processing');
                fileCard.classList.add('completed');
                break;
                
            case 'error':
                statusText.textContent = 'Error';
                progressContainer.style.display = 'none';
                fileCard.classList.remove('processing');
                fileCard.classList.add('error');
                break;
                
            default:
                statusText.textContent = 'Ready';
                progressContainer.style.display = 'none';
                fileCard.classList.remove('processing', 'completed', 'error');
        }
        
        // Update progress if provided
        if (progress !== null && progressFill && progressText) {
            const percentage = Math.round(progress * 100);
            progressFill.style.width = `${percentage}%`;
            progressText.textContent = `${percentage}%`;
        }
    }
    
    getDefaultThumbnail(fileType) {
        // Return a default thumbnail based on file type
        const canvas = document.createElement('canvas');
        canvas.width = 150;
        canvas.height = 150;
        const ctx = canvas.getContext('2d');
        
        // Draw default thumbnail
        ctx.fillStyle = '#f3f4f6';
        ctx.fillRect(0, 0, 150, 150);
        
        ctx.fillStyle = '#9ca3af';
        ctx.font = '12px Arial';
        ctx.textAlign = 'center';
        ctx.fillText('Image', 75, 70);
        ctx.fillText('Preview', 75, 85);
        ctx.fillText('Not Available', 75, 100);
        
        return canvas.toDataURL();
    }
    
    // Public methods for external access
    getFiles() {
        return this.files;
    }
    
    getFileById(fileId) {
        return this.files.find(f => f.id === fileId);
    }
    
    getFileCount() {
        return this.files.length;
    }
    
    getTotalSize() {
        return this.currentTotalSize;
    }
    
    canAddMoreFiles() {
        return this.files.length < this.maxFiles;
    }
    
    getRemainingSize() {
        return this.maxTotalSize - this.currentTotalSize;
    }
    
    // Validation methods
    validateFiles() {
        const errors = [];
        
        if (this.files.length === 0) {
            errors.push('No files selected. Please add at least one image file.');
        }
        
        if (this.files.length > this.maxFiles) {
            errors.push(`Too many files. Maximum ${this.maxFiles} files allowed.`);
        }
        
        if (this.currentTotalSize > this.maxTotalSize) {
            errors.push(`Total file size exceeds limit. Maximum ${Utils.formatFileSize(this.maxTotalSize)} allowed.`);
        }
        
        return {
            isValid: errors.length === 0,
            errors: errors
        };
    }
}

// Initialize file handler when DOM is loaded
let fileHandler;

document.addEventListener('DOMContentLoaded', () => {
    fileHandler = new FileHandler();
    
    // Make it globally accessible
    window.FileHandler = fileHandler;
});

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = FileHandler;
}