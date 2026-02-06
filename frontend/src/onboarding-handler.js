import {
    getOnboardingProgress,
    createCompany,
    selectIntegration,
    triggerFirstScan,
    ONBOARDING_STEPS,
    COMPANY_SIZES,
    INDUSTRIES,
    SSO_PROVIDERS
} from './lib/onboarding.js';
import { getUser } from './lib/auth.js';

const ONBOARDING_CONTAINER_ID = 'onboarding-view';

/**
 * Main Onboarding Handler
 */
class OnboardingHandler {
    constructor() {
        this.user = null;
        this.progress = null;
        this.currentStep = 1;
        this.container = document.getElementById(ONBOARDING_CONTAINER_ID);
    }

    async init() {
        const { user, error: authError } = await getUser();
        if (authError || !user) {
            window.location.href = '/login.html';
            return;
        }
        this.user = user;

        const { progress, error: progError } = await getOnboardingProgress(user.id);
        if (progError) {
            console.error('Error loading progress:', progError);
            return;
        }
        this.progress = progress;

        if (progress.is_onboarding_complete) {
            window.location.href = '/dashboard.html';
            return;
        }

        this.determineCurrentStep();
        this.render();
    }

    determineCurrentStep() {
        const step = this.progress.step_completed;
        if (!step) this.currentStep = 1;
        else if (step === ONBOARDING_STEPS.CONNECT_COMPANY) this.currentStep = 2;
        else if (step === ONBOARDING_STEPS.CHOOSE_INTEGRATION) this.currentStep = 3;
        else this.currentStep = 1;

        this.updateStepper();
    }

    updateStepper() {
        const steps = document.querySelectorAll('.step');
        steps.forEach((el, index) => {
            const stepNum = index + 1;
            el.classList.remove('active', 'completed');
            if (stepNum === this.currentStep) el.classList.add('active');
            else if (stepNum < this.currentStep) el.classList.add('completed');
        });
    }

    render() {
        this.container.innerHTML = '';

        switch (this.currentStep) {
            case 1:
                this.renderStep1();
                break;
            case 2:
                this.renderStep2();
                break;
            case 3:
                this.renderStep3();
                break;
        }
    }

    renderStep1() {
        this.container.innerHTML = `
            <div class="onboarding-card">
                <h2>🏢 Connect Your Company</h2>
                <p class="subtitle">Tell us about your organization to personalize your reports.</p>
                
                <form id="step1-form">
                    <div class="form-group">
                        <label>Company Name</label>
                        <input type="text" id="company_name" placeholder="e.g. Acme Corp" required>
                    </div>
                    
                    <div class="form-group">
                        <label>Company Size</label>
                        <select id="company_size" required>
                            <option value="">Select size...</option>
                            ${COMPANY_SIZES.map(s => `<option value="${s.value}">${s.label}</option>`).join('')}
                        </select>
                    </div>
                    
                    <div class="form-group">
                        <label>Industry</label>
                        <select id="industry" required>
                            <option value="">Select industry...</option>
                            ${INDUSTRIES.map(i => `<option value="${i.value}">${i.label}</option>`).join('')}
                        </select>
                    </div>
                    
                    <button type="submit" class="btn-primary" id="submit-step1">Continue to Integrations →</button>
                    <p id="step1-error" class="error-text" style="color: #ff6b6b; margin-top: 1rem; display: none;"></p>
                </form>
            </div>
        `;

        const form = document.getElementById('step1-form');
        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            const btn = document.getElementById('submit-step1');
            const errorEl = document.getElementById('step1-error');

            btn.disabled = true;
            btn.innerText = 'Initializing...';
            errorEl.style.display = 'none';

            const data = {
                company_name: document.getElementById('company_name').value,
                company_size: document.getElementById('company_size').value,
                industry: document.getElementById('industry').value
            };

            const { error } = await createCompany(this.user.id, data);

            if (error) {
                errorEl.innerText = error.message;
                errorEl.style.display = 'block';
                btn.disabled = false;
                btn.innerText = 'Continue to Integrations →';
            } else {
                this.currentStep = 2;
                this.updateStepper();
                this.render();
            }
        });
    }

    renderStep2() {
        this.container.innerHTML = `
            <div class="onboarding-card">
                <h2>🔗 Choose Integration</h2>
                <p class="subtitle">Select your primary identity provider to find unused licenses automatically.</p>
                
                <div class="integrations-grid">
                    ${SSO_PROVIDERS.map(p => `
                        <div class="integration-card" data-id="${p.id}">
                            <div class="integration-icon">${p.icon}</div>
                            <div class="integration-info">
                                <h3>${p.name}</h3>
                                <p>${p.description}</p>
                            </div>
                        </div>
                    `).join('')}
                </div>
                
                <div style="margin-top: 2rem; display: flex; gap: 1rem;">
                    <button class="btn-secondary" id="skip-step2" style="background: none; border: 1px solid var(--border-glass); color: white; padding: 0.8rem; border-radius: 8px; flex: 1; cursor: pointer;">Skip for now</button>
                    <button class="btn-primary" id="submit-step2" style="flex: 2;" disabled>Connect & Continue →</button>
                </div>
            </div>
        `;

        let selectedId = null;
        const cards = document.querySelectorAll('.integration-card');
        const submitBtn = document.getElementById('submit-step2');

        cards.forEach(card => {
            card.addEventListener('click', () => {
                cards.forEach(c => c.classList.remove('selected'));
                card.classList.add('selected');
                selectedId = card.dataset.id;
                submitBtn.disabled = false;
            });
        });

        submitBtn.addEventListener('click', async () => {
            submitBtn.disabled = true;
            submitBtn.innerText = 'Connecting...';
            const { error } = await selectIntegration(this.user.id, selectedId);
            if (!error) {
                this.currentStep = 3;
                this.updateStepper();
                this.render();
            } else {
                alert(error.message);
                submitBtn.disabled = false;
                submitBtn.innerText = 'Connect & Continue →';
            }
        });

        document.getElementById('skip-step2').addEventListener('click', async () => {
            const { error } = await selectIntegration(this.user.id, null, true);
            if (!error) {
                this.currentStep = 3;
                this.updateStepper();
                this.render();
            }
        });
    }

    renderStep3() {
        this.container.innerHTML = `
            <div class="onboarding-card">
                <h2>🔍 Your First Scan</h2>
                <p class="subtitle">We're about to run a deep scan to find hidden SaaS waste in your company.</p>
                
                <div id="scan-container">
                    <div class="scan-summary">
                        <img src="https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExOHI4eXV4ZjZkZ2RhZ2RhZ2RhZ2RhZ2RhZ2RhZ2RhZ2RhZ2RhJmVwPXYxX2ludGVybmFsX2dpZl9ieV9pZCZjdD1n/3o7TKMGpxVfFES4t6o/giphy.gif" width="120" style="margin-bottom: 1rem; border-radius: 50%;">
                        <p>Ready to find the ghosts?</p>
                        <button class="btn-primary" id="start-scan">Launch Deep Scan 🚀</button>
                    </div>
                </div>
            </div>
        `;

        document.getElementById('start-scan').addEventListener('click', async () => {
            const container = document.getElementById('scan-container');
            container.innerHTML = `
                <div class="scan-summary">
                    <p>Scanning 2,400+ SaaS vendors...</p>
                    <div class="progress-bar-container">
                        <div class="progress-bar-fill" id="scan-progress"></div>
                    </div>
                    <p id="scan-status" class="status-text">Analyzing Google Workspace logs...</p>
                </div>
            `;

            const fill = document.getElementById('scan-progress');
            const status = document.getElementById('scan-status');

            // Progress animation
            let progress = 0;
            const statuses = [
                'Analyzing Google Workspace logs...',
                'Fetching user activity data...',
                'Cross-referencing with 2,400+ SaaS vendors...',
                'Detecting unused licenses...',
                'Calculating potential savings...'
            ];

            const interval = setInterval(() => {
                progress += 1;
                fill.style.width = `${progress}%`;
                if (progress % 20 === 0) {
                    status.innerText = statuses[Math.floor(progress / 20) - 1] || statuses[statuses.length - 1];
                }
                if (progress >= 100) {
                    clearInterval(interval);
                }
            }, 30);

            const { results, error } = await triggerFirstScan(this.user.id);

            if (progress < 100) {
                progress = 100;
                fill.style.width = '100%';
            }

            if (!error && results) {
                setTimeout(() => {
                    this.renderScanResults(results);
                }, 500);
            } else {
                alert(error?.message || 'Error running scan');
            }
        });
    }

    renderScanResults(results) {
        const formatCurrency = (amount) => new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(amount);

        this.container.innerHTML = `
            <div class="onboarding-card" style="max-width: 600px;">
                <div class="scan-summary">
                    <h2 style="color: var(--color-success);">Scan Complete! 🎉</h2>
                    <p>We found significant waste in your company.</p>
                    
                    <span class="scan-label">Annual Potential Savings</span>
                    <span class="scan-value">${formatCurrency(results.potential_savings)}</span>
                    
                    <div style="background: rgba(255, 255, 255, 0.05); padding: 1.5rem; border-radius: 12px; margin-bottom: 2rem;">
                        <p style="margin: 0;">Found <strong>${results.ghost_licenses}</strong> ghost licenses across <strong>${results.top_ghost_apps.length}</strong> top apps.</p>
                    </div>

                    <button class="btn-primary" id="finish-onboarding">Go to My Dashboard →</button>
                    <p style="margin-top: 1rem; font-size: 0.8rem; color: var(--text-muted);">You've just saved more than the cost of Ghost License Reaper for 5 years.</p>
                </div>
            </div>
        `;

        document.getElementById('finish-onboarding').addEventListener('click', () => {
            window.location.href = '/dashboard.html';
        });
    }
}

// Start onboarding
const handler = new OnboardingHandler();
handler.init();
