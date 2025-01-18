// app/static/js/analysis.js

class AnalysisHandler {
    constructor() {
        this.resultsContainer = document.getElementById('analysisResults');
        this.accordion = document.getElementById('analysisAccordion');
    }

    displayResults(analysisData) {
        // Show results container
        this.resultsContainer.classList.remove('d-none');
        this.resultsContainer.classList.add('slide-up');

        // Clear previous results
        this.accordion.innerHTML = '';

        // Create sections
        const sections = [
            { id: 'summary', title: '文档摘要', icon: 'file-text' },
            { id: 'character', title: '人物分析', icon: 'users' },
            { id: 'plot', title: '情节分析', icon: 'book-open' },
            { id: 'theme', title: '主题分析', icon: 'layers' },
            { id: 'readability', title: '可读性评估', icon: 'check-square' },
            { id: 'sentiment', title: '情感分析', icon: 'heart' },
            { id: 'style', title: '风格一致性', icon: 'edit-3' }
        ];

        sections.forEach((section, index) => {
            const content = this.getContentForSection(analysisData, section.id);
            if (content) {
                this.createAccordionItem(section, content, index === 0);
            }
        });
    }

    getContentForSection(data, sectionId) {
        const mappings = {
            'summary': data.summary,
            'character': data.character_analysis,
            'plot': data.plot_analysis,
            'theme': data.theme_analysis,
            'readability': this.formatReadabilityScore(data.readability_score),
            'sentiment': this.formatSentimentAnalysis(data.sentiment_score),
            'style': data.style_consistency
        };
        return mappings[sectionId];
    }

    createAccordionItem(section, content, isFirst = false) {
        const itemHtml = `
            <div class="accordion-item">
                <h2 class="accordion-header">
                    <button class="accordion-button ${!isFirst ? 'collapsed' : ''}" 
                            type="button" 
                            data-bs-toggle="collapse" 
                            data-bs-target="#${section.id}-collapse"
                            aria-expanded="${isFirst ? 'true' : 'false'}"
                            aria-controls="${section.id}-collapse">
                        <i class="fas fa-${section.icon} me-2"></i>
                        ${section.title}
                    </button>
                </h2>
                <div id="${section.id}-collapse" 
                     class="accordion-collapse collapse ${isFirst ? 'show' : ''}"
                     data-bs-parent="#analysisAccordion">
                    <div class="accordion-body">
                        ${this.formatContent(content)}
                    </div>
                </div>
            </div>
        `;

        this.accordion.insertAdjacentHTML('beforeend', itemHtml);
    }

    formatContent(content) {
        if (typeof content === 'number') {
            return this.createProgressBar(content);
        }

        // Convert markdown-style content to HTML
        return content
            .replace(/\n\n/g, '</p><p>')
            .replace(/\n/g, '<br>')
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            .trim();
    }

    formatReadabilityScore(score) {
        if (!score) return null;

        const levels = {
            90: '非常容易理解',
            80: '容易理解',
            70: '较易理解',
            60: '中等难度',
            50: '较难理解',
            40: '难理解',
            0: '非常难理解'
        };

        let assessment = '非常难理解';
        for (const [threshold, level] of Object.entries(levels)) {
            if (score >= threshold) {
                assessment = level;
                break;
            }
        }

        return `
            <div class="mb-3">
                ${this.createProgressBar(score)}
            </div>
            <p>可读性评估：<strong>${assessment}</strong></p>
            <p>基于文本的语言复杂度、句子结构和词汇难度等因素的综合评分。</p>
        `;
    }

    formatSentimentAnalysis(score) {
        if (!score) return null;

        const sentiments = {
            80: ['非常积极', 'text-success'],
            60: ['积极', 'text-success'],
            40: ['中性', 'text-info'],
            20: ['消极', 'text-warning'],
            0: ['非常消极', 'text-danger']
        };

        let [sentiment, className] = ['非常消极', 'text-danger'];
        for (const [threshold, [label, color]] of Object.entries(sentiments)) {
            if (score >= threshold) {
                sentiment = label;
                className = color;
                break;
            }
        }

        return `
            <div class="mb-3">
                ${this.createProgressBar(score)}
            </div>
            <p>情感倾向：<strong class="${className}">${sentiment}</strong></p>
            <p>基于文本的情感色彩、语气和表达方式的分析结果。</p>
        `;
    }

    createProgressBar(value) {
        const percentage = Math.round(value);
        let colorClass = 'bg-primary';

        if (percentage >= 80) colorClass = 'bg-success';
        else if (percentage >= 60) colorClass = 'bg-info';
        else if (percentage >= 40) colorClass = 'bg-warning';
        else colorClass = 'bg-danger';

        return `
            <div class="progress" style="height: 25px">
                <div class="progress-bar ${colorClass}" 
                     role="progressbar" 
                     style="width: ${percentage}%" 
                     aria-valuenow="${percentage}" 
                     aria-valuemin="0" 
                     aria-valuemax="100">
                    ${percentage}%
                </div>
            </div>
        `;
    }

    exportResults() {
        try {
            // Create download link for results
            const content = JSON.stringify(this.currentResults, null, 2);
            const blob = new Blob([content], { type: 'application/json' });
            const url = window.URL.createObjectURL(blob);
            const link = document.createElement('a');

            link.href = url;
            link.download = `analysis-results-${new Date().toISOString()}.json`;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            window.URL.revokeObjectURL(url);

            utils.showToast('Results exported successfully');
        } catch (error) {
            utils.showToast('Failed to export results', 'error');
            console.error('Export error:', error);
        }
    }
}

// Initialize analysis handler when document is ready
document.addEventListener('DOMContentLoaded', () => {
    window.analysisHandler = new AnalysisHandler();

    // Add export button event listener if it exists
    const exportButton = document.getElementById('exportButton');
    if (exportButton) {
        exportButton.addEventListener('click', () => {
            window.analysisHandler.exportResults();
        });
    }
});