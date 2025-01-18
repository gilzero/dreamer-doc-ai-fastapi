// app/static/js/payment.js

class PaymentHandler {
    constructor() {
        this.stripe = null;
        this.elements = null;
        this.paymentElement = null;
        this.documentId = null;

        this.form = document.getElementById('payment-form');
        this.submitButton = document.getElementById('submit-button');
    }

    initialize(data) {
        // Initialize Stripe
        this.stripe = Stripe(window.config.stripePublicKey);
        this.documentId = data.id;

        // Create payment element
        this.elements = this.stripe.elements({
            clientSecret: data.payment_intent,
            appearance: {
                theme: document.documentElement.getAttribute('data-bs-theme')
            }
        });

        // Create and mount payment element
        this.paymentElement = this.elements.create('payment');
        this.paymentElement.mount('#payment-element');

        // Set up form submission
        this.form.addEventListener('submit', (e) => this.handleSubmit(e));
    }

    async handleSubmit(e) {
        e.preventDefault();

        try {
            this.setLoading(true);

            // Confirm payment
            const result = await this.stripe.confirmPayment({
                elements: this.elements,
                confirmParams: {
                    return_url: window.location.origin,
                },
                redirect: 'if_required'
            });

            if (result.error) {
                throw new Error(result.error.message);
            }

            // Process analysis
            await this.processAnalysis(result.paymentIntent.id);

        } catch (error) {
            utils.showToast(error.message, 'error');
        } finally {
            this.setLoading(false);
        }
    }

    async processAnalysis(paymentIntentId) {
        try {
            const response = await utils.fetchWithError(
                `${window.config.apiBaseUrl}/payments/process/${this.documentId}`,
                {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        payment_intent_id: paymentIntentId,
                        analysis_options: this.getAnalysisOptions()
                    })
                }
            );

            // Show analysis results
            window.analysisHandler.displayResults(response.analysis);
            utils.showToast('Payment successful. Analysis started.');

        } catch (error) {
            console.error('Analysis error:', error);
            throw new Error('Failed to start analysis');
        }
    }

    getAnalysisOptions() {
        // Get selected analysis options
        return {
            character_analysis: true,
            plot_analysis: true,
            theme_analysis: true,
            readability_assessment: true,
            sentiment_analysis: true,
            style_consistency: true
        };
    }

    setLoading(isLoading) {
        if (isLoading) {
            this.submitButton.disabled = true;
            this.submitButton.innerHTML = `
                <span class="spinner-border spinner-border-sm me-2"></span>
                Processing...
            `;
        } else {
            this.submitButton.disabled = false;
            this.submitButton.innerHTML = 'Process Payment';
        }
    }
}

// Initialize payment handler when document is ready
document.addEventListener('DOMContentLoaded', () => {
    window.paymentHandler = new PaymentHandler();
});