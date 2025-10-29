/**
 * Main Application Logic for Image to GIF Converter
 * Initializes the application and coordinates between different modules
 */

class ImageToGifApp {
    constructor() {
        this.isInitialized = false;
        this.components = {};
        
        this.init();
    }
    
    async init() {
        try {
            // Check browser compatibility
            this.checkBrowserCompatibility();
            
            // Initialize components
            await this.initializeComponents();
            
            // Setup global event listeners
            this.setupGlobalEventListeners();
            
            // Setup keyboard shortcuts
            this.setupKeyboardShortcuts();
            
            // Initialize UI state
            this.initializeUIState();
            
            // Show welcome message
            this.showWelcomeMessage();
            
            this.isInitialized = true;
            
            console.log('Image to GIF Converter initialized successfully');
            
        } catch (error) {
            Utils.ErrorHandler.logError(error, 'App initialization');
            Utils.ErrorHandler.showError('Failed to initialize application. Please refresh the page.');
        }
    }
    
    checkBrowserCompatibility() {
        const compatibility = Utils.BrowserSupport.getCompatibilityStatus();
        
        if (!compatibility.overall) {
            const missingFeatures = [];
            
            if (!compatibility.fileAPI) missingFeatures.push('File API');
            if (!compatibility.canvas) missingFeatures.push('Canvas API');
            
            const message = `Your browser doesn't support required features: ${missingFeatures.join(', ')}. Please use a modern browser.`;
            Utils.ErrorHandler.showError(message);
            
            // Disable main functionality
            this.disableApp();
            return false;
        }
        
        // Show warnings for optional features
        if (!compatibility.dragAndDrop) {
            console.warn('Drag and drop not supported. File selection will be limited to browse button.');
        }
        
        if (!compatibility.webWorkers) {
            console.warn('Web Workers not supported. GIF conversion may be slower.');
        }
        
        return true;
    }
    
    async initializeComponents() {
        // Wait for DOM to be fully loaded
        if (document.readyState !== 'complete') {
            await new Promise(resolve => {
                window.addEventListener('load', resolve);
            });
        }
        
        // Initialize components (they should already be initialized by their own scripts)
        this.components.fileHandler = window.FileHandler;
        this.components.gifConverter = window.GifConverter;
        this.components.utils = window.Utils;
        
        // Verify components are loaded
        if (!this.components.fileHandler) {
            throw new Error('FileHandler not initialized');
        }
        
        if (!this.components.gifConverter) {
            throw new Error('GifConverter not initialized');
        }
        
        if (!this.components.utils) {
            throw new Error('Utils not initialized');
        }
    }
    
    setupGlobalEventListeners() {
        // Handle window resize
        window.addEventListener('resize', Utils.debounce(() => {
            this.handleWindowResize();
        }, 250));
        
        // Handle visibility change (tab switching)
        document.addEventListener('visibilitychange', () => {
            this.handleVisibilityChange();
        });
        
        // Handle beforeunload (warn about unsaved work)
        window.addEventListener('beforeunload', (e) => {
            if (this.hasUnsavedWork()) {
                e.preventDefault();
                e.returnValue = 'You have files ready for conversion. Are you sure you want to leave?';
                return e.returnValue;
            }
        });
        
        // Handle online/offline status
        window.addEventListener('online', () => {
            Utils.ErrorHandler.showSuccess('Connection restored');
        });
        
        window.addEventListener('offline', () => {
            Utils.ErrorHandler.showError('Connection lost. The app will continue to work offline.');
        });
        
        // Handle errors globally
        window.addEventListener('error', (e) => {
            Utils.ErrorHandler.logError(e.error, 'Global error handler');
        });
        
        window.addEventListener('unhandledrejection', (e) => {
            Utils.ErrorHandler.logError(e.reason, 'Unhandled promise rejection');
        });
    }
    
    setupKeyboardShortcuts() {
        document.addEventListener('keydown', (e) => {
            // Ctrl/Cmd + O: Open files
            if ((e.ctrlKey || e.metaKey) && e.key === 'o') {
                e.preventDefault();
                document.getElementById('file-input').click();
            }
            
            // Ctrl/Cmd + Enter: Start conversion
            if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
                e.preventDefault();
                const convertBtn = document.getElementById('convert-btn');
                if (!convertBtn.disabled) {
                    convertBtn.click();
                }
            }
            
            // Escape: Clear files or cancel conversion
            if (e.key === 'Escape') {
                if (this.components.gifConverter.isConverting) {
                    // Note: gif.js doesn't support cancellation, but we can show a message
                    Utils.ErrorHandler.showError('Conversion cannot be cancelled once started.');
                } else if (this.components.fileHandler.getFileCount() > 0) {
                    if (confirm('Clear all files?')) {
                        this.components.fileHandler.clearAllFiles();
                    }
                }
            }
            
            // Ctrl/Cmd + A: Select all (prevent default to avoid selecting page content)
            if ((e.ctrlKey || e.metaKey) && e.key === 'a') {
                const activeElement = document.activeElement;
                if (!activeElement || !['INPUT', 'TEXTAREA'].includes(activeElement.tagName)) {
                    e.preventDefault();
                }
            }
        });
    }
    
    initializeUIState() {
        // Set initial theme
        this.applyTheme();
        
        // Initialize tooltips
        this.initializeTooltips();
        
        // Initialize animations
        this.initializeAnimations();
        
        // Set initial focus
        this.setInitialFocus();
        
        // Update UI based on stored settings
        this.restoreUIState();
    }
    
    applyTheme() {
        // Check for system dark mode preference
        const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
        const savedTheme = localStorage.getItem('theme');
        
        const theme = savedTheme || (prefersDark ? 'dark' : 'light');
        document.documentElement.setAttribute('data-theme', theme);
        
        // Listen for system theme changes
        window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
            if (!localStorage.getItem('theme')) {
                document.documentElement.setAttribute('data-theme', e.matches ? 'dark' : 'light');
            }
        });
    }
    
    initializeTooltips() {
        // Simple tooltip implementation
        const tooltipElements = document.querySelectorAll('[title]');
        
        tooltipElements.forEach(element => {
            let tooltip = null;
            
            element.addEventListener('mouseenter', (e) => {
                const title = element.getAttribute('title');
                if (!title) return;
                
                // Remove title to prevent default tooltip
                element.removeAttribute('title');
                element.setAttribute('data-original-title', title);
                
                // Create tooltip
                tooltip = document.createElement('div');
                tooltip.className = 'custom-tooltip';
                tooltip.textContent = title;
                tooltip.style.cssText = `
                    position: absolute;
                    background: #333;
                    color: white;
                    padding: 6px 10px;
                    border-radius: 4px;
                    font-size: 12px;
                    white-space: nowrap;
                    z-index: 10000;
                    pointer-events: none;
                    opacity: 0;
                    transition: opacity 0.2s;
                `;
                
                document.body.appendChild(tooltip);
                
                // Position tooltip
                const rect = element.getBoundingClientRect();
                tooltip.style.left = rect.left + (rect.width / 2) - (tooltip.offsetWidth / 2) + 'px';
                tooltip.style.top = rect.top - tooltip.offsetHeight - 8 + 'px';
                
                // Show tooltip
                setTimeout(() => {
                    if (tooltip) tooltip.style.opacity = '1';
                }, 100);
            });
            
            element.addEventListener('mouseleave', () => {
                if (tooltip) {
                    tooltip.remove();
                    tooltip = null;
                }
                
                // Restore original title
                const originalTitle = element.getAttribute('data-original-title');
                if (originalTitle) {
                    element.setAttribute('title', originalTitle);
                    element.removeAttribute('data-original-title');
                }
            });
        });
    }
    
    initializeAnimations() {
        // Add entrance animations to main sections
        const sections = document.querySelectorAll('.section');
        
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('animate-in');
                }
            });
        }, {
            threshold: 0.1,
            rootMargin: '0px 0px -50px 0px'
        });
        
        sections.forEach(section => {
            observer.observe(section);
        });
    }
    
    setInitialFocus() {
        // Focus on the upload area for better accessibility
        const uploadArea = document.getElementById('upload-area');
        if (uploadArea) {
            uploadArea.setAttribute('tabindex', '0');
            uploadArea.focus();
        }
    }
    
    restoreUIState() {
        // Restore any saved UI preferences
        const savedSettings = Utils.StorageUtils.loadSettings();
        if (savedSettings) {
            // Apply any UI-specific settings here
            console.log('Restored settings:', savedSettings);
        }
    }
    
    showWelcomeMessage() {
        // Show a brief welcome message
        setTimeout(() => {
            Utils.ErrorHandler.showSuccess('Welcome to Image to GIF Converter! Drag & drop images or click to browse.', 4000);
        }, 500);
    }
    
    handleWindowResize() {
        // Handle responsive adjustments that CSS can't handle
        const isMobile = window.innerWidth <= 768;
        document.body.classList.toggle('mobile-view', isMobile);
        
        // Adjust any dynamic layouts
        this.adjustDynamicLayouts();
    }
    
    handleVisibilityChange() {
        if (document.hidden) {
            // Page is hidden (user switched tabs)
            console.log('App hidden');
        } else {
            // Page is visible again
            console.log('App visible');
            
            // Check if any conversions completed while away
            this.checkConversionStatus();
        }
    }
    
    hasUnsavedWork() {
        // Check if there are files ready for conversion
        const fileCount = this.components.fileHandler ? this.components.fileHandler.getFileCount() : 0;
        const isConverting = this.components.gifConverter ? this.components.gifConverter.isConverting : false;
        
        return fileCount > 0 && !isConverting;
    }
    
    adjustDynamicLayouts() {
        // Adjust any layouts that need JavaScript calculation
        const fileCards = document.querySelectorAll('.file-card');
        
        // Ensure file cards maintain proper aspect ratios on mobile
        if (window.innerWidth <= 480) {
            fileCards.forEach(card => {
                card.classList.add('mobile-layout');
            });
        } else {
            fileCards.forEach(card => {
                card.classList.remove('mobile-layout');
            });
        }
    }
    
    checkConversionStatus() {
        // This would be useful if we had background processing
        // For now, just log that we're checking
        console.log('Checking conversion status...');
    }
    
    disableApp() {
        // Disable the app if browser is incompatible
        const mainContent = document.querySelector('main');
        if (mainContent) {
            mainContent.innerHTML = `
                <div class="compatibility-error">
                    <h2>Browser Not Supported</h2>
                    <p>This application requires a modern browser with support for:</p>
                    <ul>
                        <li>File API</li>
                        <li>Canvas API</li>
                        <li>HTML5 features</li>
                    </ul>
                    <p>Please update your browser or try a different one.</p>
                </div>
            `;
        }
    }
    
    // Public methods for external access
    getComponent(name) {
        return this.components[name];
    }
    
    isReady() {
        return this.isInitialized;
    }
    
    // Debug methods
    getDebugInfo() {
        return {
            initialized: this.isInitialized,
            components: Object.keys(this.components),
            fileCount: this.components.fileHandler ? this.components.fileHandler.getFileCount() : 0,
            browserSupport: Utils.BrowserSupport.getCompatibilityStatus(),
            performance: {
                memory: performance.memory ? {
                    used: Math.round(performance.memory.usedJSHeapSize / 1024 / 1024) + 'MB',
                    total: Math.round(performance.memory.totalJSHeapSize / 1024 / 1024) + 'MB'
                } : 'Not available'
            }
        };
    }
    
    // Performance monitoring
    startPerformanceMonitoring() {
        // Monitor memory usage
        if (performance.memory) {
            setInterval(() => {
                const memoryUsage = performance.memory.usedJSHeapSize / 1024 / 1024;
                if (memoryUsage > 100) { // Alert if using more than 100MB
                    console.warn(`High memory usage: ${Math.round(memoryUsage)}MB`);
                }
            }, 30000); // Check every 30 seconds
        }
        
        // Monitor performance
        const observer = new PerformanceObserver((list) => {
            list.getEntries().forEach((entry) => {
                if (entry.duration > 100) { // Alert for operations taking more than 100ms
                    console.warn(`Slow operation detected: ${entry.name} took ${Math.round(entry.duration)}ms`);
                }
            });
        });
        
        observer.observe({ entryTypes: ['measure'] });
    }
}

// Initialize the application when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    // Create global app instance
    window.ImageToGifApp = new ImageToGifApp();
    
    // Start performance monitoring in development
    if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
        window.ImageToGifApp.startPerformanceMonitoring();
    }
    
    // Add debug helper to console
    console.log('Image to GIF Converter loaded. Type "app.getDebugInfo()" for debug information.');
    window.app = window.ImageToGifApp;
});

// Handle any initialization errors
window.addEventListener('error', (e) => {
    if (e.filename && e.filename.includes('main.js')) {
        console.error('Main app initialization error:', e.error);
        
        // Show user-friendly error
        const errorDiv = document.createElement('div');
        errorDiv.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            background: #EF4444;
            color: white;
            padding: 15px;
            text-align: center;
            z-index: 10000;
            font-family: Arial, sans-serif;
        `;
        errorDiv.innerHTML = `
            <strong>Application Error:</strong> Failed to initialize. Please refresh the page.
            <button onclick="location.reload()" style="margin-left: 10px; padding: 5px 10px; background: white; color: #EF4444; border: none; border-radius: 3px; cursor: pointer;">
                Refresh
            </button>
        `;
        
        document.body.insertBefore(errorDiv, document.body.firstChild);
    }
});

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ImageToGifApp;
}