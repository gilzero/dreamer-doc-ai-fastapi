// app/static/js/upload.js

class FileUploader {
    constructor() {
        this.uploadZone = document.getElementById('uploadZone');
        this.fileInput = document.getElementById('fileInput');
        this.documentInfo = document.getElementById('documentInfo');
        this.currentFile = null;

        this.initializeEventListeners();
    }

    initializeEventListeners() {
        // Drag and drop events
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            this.uploadZone.addEventListener(eventName, (e) => {
                e.preventDefault();
                e.stopPropagation();
            });
        });

        // Add dragover and dragleave styling
        ['dragenter', 'dragover'].forEach(eventName => {
            this.uploadZone.addEventListener(eventName, () => {
                this.uploadZone.classList.add('dragover');
            });
        });

        ['dragleave', 'drop'].forEach(eventName => {
            this.uploadZone.addEventListener(eventName, () => {
                this.uploadZone.classList.remove('dragover');
            });
        });

        // Handle file drop
        this.uploadZone.addEventListener('drop', (e) => {
            const files = e.dataTransfer.files;
            if (files.length) this.handleFile(files[0]);
        });

        // Handle file selection
        this.fileInput.addEventListener('change', (e) => {
            if (e.target.files.length) this.handleFile(e.target.files[0]);
        });
    }

    async handleFile(file) {
        try {
            // Validate file
            if (!this.validateFile(file)) return;

            this.currentFile = file;
            utils.showLoading();

            // Create FormData
            const formData = new FormData();
            formData.append('file', file);

            // Upload file
            const response = await utils.fetchWithError(
                `${window.config.apiBaseUrl}/documents/upload`,
                {
                    method: 'POST',
                    body: formData
                }
            );

            // Update UI
            this.updateDocumentInfo(response);
            this.showPaymentSection(response);

            utils.showToast('File uploaded successfully');

        } catch (error) {
            console.error('Upload error:', error);
        } finally {
            utils.hideLoading();
        }
    }

    validateFile(file) {
        // Check file type
        const allowedTypes = ['application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'];
        if (!allowedTypes.includes(file.type)) {
            utils.showToast('Please upload a PDF or Word document', 'error');
            return false;
        }

        // Check file size (20MB max)
        if (file.size > 20 * 1024 * 1024) {
            utils.showToast('File size must be less than 20MB', 'error');
            return false;
        }

        return true;
    }

    updateDocumentInfo(data) {
        // Update document info display
        document.getElementById('docTitle').textContent = data.title || 'Untitled';
        document.getElementById('docSize').textContent = utils.formatBytes(data.file_size);
        document.getElementById('docCharCount').textContent = data.char_count.toLocaleString();
        document.getElementById('docCost').textContent = `¥${(data.analysis_cost / 100).toFixed(2)}`;
        document.getElementById('docDate').textContent = utils.formatDate(data.created_at);
        document.getElementById('docStatus').textContent = data.status;

        // Show document info section
        this.documentInfo.classList.remove('d-none');
        this.documentInfo.classList.add('slide-up');
    }

    showPaymentSection(data) {
        // Initialize payment handling
        window.paymentHandler.initialize(data);
        document.getElementById('paymentSection').classList.remove('d-none');
    }
}

// Initialize uploader when document is ready
document.addEventListener('DOMContentLoaded', () => {
    window.fileUploader = new FileUploader();
});