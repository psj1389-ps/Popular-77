/**
 * Utility functions for Image to GIF Converter
 */

// File size formatting utility
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// File type validation
function isValidImageFile(file) {
    const validTypes = [
        'image/jpeg',
        'image/jpg', 
        'image/png',
        'image/webp',
        'image/bmp',
        'image/tiff',
        'image/svg+xml',
        'image/x-photoshop', // PSD
        'image/vnd.adobe.photoshop', // PSD
        'image/heic',
        'image/heif',
        'image/x-canon-cr2', // RAW
        'image/x-canon-crw', // RAW
        'image/x-nikon-nef', // RAW
        'image/x-sony-arw', // RAW
        'image/x-adobe-dng', // RAW
        'image/gif' // Allow GIF input as well
    ];
    
    // Check MIME type
    if (validTypes.includes(file.type)) {
        return true;
    }
    
    // Fallback: check file extension
    const fileName = file.name.toLowerCase();
    const validExtensions = [
        '.jpg', '.jpeg', '.png', '.webp', '.bmp', '.tiff', '.tif',
        '.svg', '.psd', '.heic', '.heif', '.cr2', '.crw', '.nef',
        '.arw', '.dng', '.raw', '.gif'
    ];
    
    return validExtensions.some(ext => fileName.endsWith(ext));
}

// Get file extension
function getFileExtension(filename) {
    return filename.slice((filename.lastIndexOf(".") - 1 >>> 0) + 2).toLowerCase();
}

// Generate unique filename
function generateUniqueFilename(originalName, suffix = '') {
    const extension = getFileExtension(originalName);
    const nameWithoutExt = originalName.substring(0, originalName.lastIndexOf('.'));
    const timestamp = Date.now();
    
    return `${nameWithoutExt}${suffix}_${timestamp}.${extension}`;
}

// Create thumbnail from file
function createThumbnail(file, maxWidth = 150, maxHeight = 150) {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        
        reader.onload = function(e) {
            const img = new Image();
            
            img.onload = function() {
                const canvas = document.createElement('canvas');
                const ctx = canvas.getContext('2d');
                
                // Calculate thumbnail dimensions
                let { width, height } = calculateThumbnailSize(
                    img.width, 
                    img.height, 
                    maxWidth, 
                    maxHeight
                );
                
                canvas.width = width;
                canvas.height = height;
                
                // Draw thumbnail
                ctx.drawImage(img, 0, 0, width, height);
                
                // Convert to data URL
                const thumbnailDataUrl = canvas.toDataURL('image/jpeg', 0.8);
                resolve(thumbnailDataUrl);
            };
            
            img.onerror = () => reject(new Error('Failed to load image'));
            img.src = e.target.result;
        };
        
        reader.onerror = () => reject(new Error('Failed to read file'));
        reader.readAsDataURL(file);
    });
}

// Calculate thumbnail size maintaining aspect ratio
function calculateThumbnailSize(originalWidth, originalHeight, maxWidth, maxHeight) {
    let width = originalWidth;
    let height = originalHeight;
    
    // Calculate scaling factor
    const widthRatio = maxWidth / originalWidth;
    const heightRatio = maxHeight / originalHeight;
    const ratio = Math.min(widthRatio, heightRatio);
    
    // Apply scaling if needed
    if (ratio < 1) {
        width = Math.round(originalWidth * ratio);
        height = Math.round(originalHeight * ratio);
    }
    
    return { width, height };
}

// Debounce function for performance optimization
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Throttle function for performance optimization
function throttle(func, limit) {
    let inThrottle;
    return function() {
        const args = arguments;
        const context = this;
        if (!inThrottle) {
            func.apply(context, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}

// Download file utility
function downloadFile(blob, filename) {
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}

// Create ZIP file for multiple downloads
async function createZipFile(files) {
    // Simple ZIP creation (for modern browsers)
    // Note: This is a basic implementation. For production, consider using JSZip library
    const zip = new Map();
    
    for (const file of files) {
        zip.set(file.name, file.blob);
    }
    
    return zip;
}

// Local storage utilities
const StorageUtils = {
    // Save user settings
    saveSettings(settings) {
        try {
            localStorage.setItem('gifConverter_settings', JSON.stringify(settings));
            return true;
        } catch (error) {
            console.error('Failed to save settings:', error);
            return false;
        }
    },
    
    // Load user settings
    loadSettings() {
        try {
            const settings = localStorage.getItem('gifConverter_settings');
            return settings ? JSON.parse(settings) : null;
        } catch (error) {
            console.error('Failed to load settings:', error);
            return null;
        }
    },
    
    // Clear all stored data
    clearAll() {
        try {
            localStorage.removeItem('gifConverter_settings');
            return true;
        } catch (error) {
            console.error('Failed to clear storage:', error);
            return false;
        }
    }
};

// Error handling utilities
const ErrorHandler = {
    // Show user-friendly error message
    showError(message, duration = 5000) {
        const errorDiv = document.createElement('div');
        errorDiv.className = 'error-toast';
        errorDiv.textContent = message;
        errorDiv.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: #EF4444;
            color: white;
            padding: 12px 20px;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            z-index: 10000;
            font-size: 14px;
            max-width: 300px;
            word-wrap: break-word;
        `;
        
        document.body.appendChild(errorDiv);
        
        setTimeout(() => {
            if (errorDiv.parentNode) {
                errorDiv.parentNode.removeChild(errorDiv);
            }
        }, duration);
    },
    
    // Show success message
    showSuccess(message, duration = 3000) {
        const successDiv = document.createElement('div');
        successDiv.className = 'success-toast';
        successDiv.textContent = message;
        successDiv.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: #10B981;
            color: white;
            padding: 12px 20px;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            z-index: 10000;
            font-size: 14px;
            max-width: 300px;
            word-wrap: break-word;
        `;
        
        document.body.appendChild(successDiv);
        
        setTimeout(() => {
            if (successDiv.parentNode) {
                successDiv.parentNode.removeChild(successDiv);
            }
        }, duration);
    },
    
    // Log error for debugging
    logError(error, context = '') {
        console.error(`[GIF Converter Error] ${context}:`, error);
        
        // In production, you might want to send this to an error tracking service
        // Example: Sentry, LogRocket, etc.
    }
};

// Animation utilities
const AnimationUtils = {
    // Fade in element
    fadeIn(element, duration = 300) {
        element.style.opacity = '0';
        element.style.display = 'block';
        
        let start = null;
        function animate(timestamp) {
            if (!start) start = timestamp;
            const progress = timestamp - start;
            const opacity = Math.min(progress / duration, 1);
            
            element.style.opacity = opacity;
            
            if (progress < duration) {
                requestAnimationFrame(animate);
            }
        }
        
        requestAnimationFrame(animate);
    },
    
    // Fade out element
    fadeOut(element, duration = 300) {
        let start = null;
        const initialOpacity = parseFloat(getComputedStyle(element).opacity);
        
        function animate(timestamp) {
            if (!start) start = timestamp;
            const progress = timestamp - start;
            const opacity = Math.max(initialOpacity - (progress / duration), 0);
            
            element.style.opacity = opacity;
            
            if (progress < duration) {
                requestAnimationFrame(animate);
            } else {
                element.style.display = 'none';
            }
        }
        
        requestAnimationFrame(animate);
    }
};

// Performance monitoring
const PerformanceMonitor = {
    timers: new Map(),
    
    start(label) {
        this.timers.set(label, performance.now());
    },
    
    end(label) {
        const startTime = this.timers.get(label);
        if (startTime) {
            const duration = performance.now() - startTime;
            console.log(`[Performance] ${label}: ${duration.toFixed(2)}ms`);
            this.timers.delete(label);
            return duration;
        }
        return null;
    }
};

// Browser compatibility checks
const BrowserSupport = {
    // Check if File API is supported
    hasFileAPI() {
        return !!(window.File && window.FileReader && window.FileList && window.Blob);
    },
    
    // Check if Canvas API is supported
    hasCanvas() {
        const canvas = document.createElement('canvas');
        return !!(canvas.getContext && canvas.getContext('2d'));
    },
    
    // Check if Web Workers are supported
    hasWebWorkers() {
        return !!window.Worker;
    },
    
    // Check if drag and drop is supported
    hasDragAndDrop() {
        const div = document.createElement('div');
        return ('draggable' in div) || ('ondragstart' in div && 'ondrop' in div);
    },
    
    // Get overall compatibility status
    getCompatibilityStatus() {
        return {
            fileAPI: this.hasFileAPI(),
            canvas: this.hasCanvas(),
            webWorkers: this.hasWebWorkers(),
            dragAndDrop: this.hasDragAndDrop(),
            overall: this.hasFileAPI() && this.hasCanvas()
        };
    }
};

// Export utilities for use in other modules
window.Utils = {
    formatFileSize,
    isValidImageFile,
    getFileExtension,
    generateUniqueFilename,
    createThumbnail,
    calculateThumbnailSize,
    debounce,
    throttle,
    downloadFile,
    createZipFile,
    StorageUtils,
    ErrorHandler,
    AnimationUtils,
    PerformanceMonitor,
    BrowserSupport
};