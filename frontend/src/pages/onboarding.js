/**
 * Onboarding Page - Ghost License Reaper
 * 3-Step Onboarding Flow
 */

import {
    ONBOARDING_STEPS, COMPANY_SIZES, INDUSTRIES, SSO_PROVIDERS,
    getOnboardingProgress, createCompany, selectIntegration, triggerFirstScan
} from '../lib/onboarding.js'
import { getUser } from '../lib/auth.js'

let currentStep = 1
let userId = null

export const initOnboardingPage = async () => {
    const { user } = await getUser()
    if (!user) {
        window.location.href = '/login'
        return
    }
    userId = user.id

    const { progress } = await getOnboardingProgress(userId)
    if (progress?.is_onboarding_complete) {
        window.location.href = '/dashboard'
        return
    }

    // Determine current step
    if (progress?.step_data?.choose_integration) currentStep = 3
    else if (progress?.step_data?.connect_company) currentStep = 2
    else currentStep = 1

    renderStep(currentStep)
    setupEventListeners()
}

function renderStep(step) {
    const container = document.getElementById('onboarding-content')
    updateProgress(step)

    switch (step) {
        case 1: container.innerHTML = renderStep1(); break
        case 2: container.innerHTML = renderStep2(); break
        case 3: container.innerHTML = renderStep3(); break
    }
}

function updateProgress(step) {
    document.querySelectorAll('.step-indicator').forEach((el, i) => {
        el.classList.toggle('active', i + 1 === step)
        el.classList.toggle('completed', i + 1 < step)
    })
}

function renderStep1() {
    return `
    <div class="onboarding-step">
      <h2>🏢 Connect Your Company</h2>
      <p>Tell us about your organization</p>
      <form id="step1-form">
        <div class="form-group">
          <label>Company Name</label>
          <input type="text" id="company-name" required placeholder="Acme Corporation">
        </div>
        <div class="form-group">
          <label>Company Size</label>
          <select id="company-size" required>
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
        <button type="submit" class="btn btn-primary">Continue →</button>
      </form>
    </div>
  `
}

function renderStep2() {
    return `
    <div class="onboarding-step">
      <h2>🔗 Choose Integration</h2>
      <p>Connect your identity provider to sync users</p>
      <div class="sso-options">
        ${SSO_PROVIDERS.map(p => `
          <button class="sso-option" data-provider="${p.id}">
            <span class="sso-icon">${p.icon}</span>
            <span class="sso-name">${p.name}</span>
            <span class="sso-desc">${p.description}</span>
          </button>
        `).join('')}
      </div>
      <button id="skip-integration" class="btn btn-secondary">Skip for now →</button>
    </div>
  `
}

function renderStep3() {
    return `
    <div class="onboarding-step">
      <h2>🔍 First Scan</h2>
      <p>Let's find your ghost licenses</p>
      <div id="scan-status">
        <button id="start-scan" class="btn btn-primary btn-lg">Start Scan 🚀</button>
      </div>
      <div id="scan-results" class="hidden"></div>
    </div>
  `
}

function setupEventListeners() {
    document.addEventListener('submit', async (e) => {
        if (e.target.id === 'step1-form') {
            e.preventDefault()
            const data = {
                company_name: document.getElementById('company-name').value,
                company_size: document.getElementById('company-size').value,
                industry: document.getElementById('industry').value
            }
            const { company, error } = await createCompany(userId, data)
            if (!error) { currentStep = 2; renderStep(2) }
        }
    })

    document.addEventListener('click', async (e) => {
        if (e.target.closest('.sso-option')) {
            const provider = e.target.closest('.sso-option').dataset.provider
            await selectIntegration(userId, provider, false)
            currentStep = 3; renderStep(3)
        }

        if (e.target.id === 'skip-integration') {
            await selectIntegration(userId, null, true)
            currentStep = 3; renderStep(3)
        }

        if (e.target.id === 'start-scan') {
            e.target.disabled = true
            e.target.innerHTML = '⏳ Scanning...'
            const { results } = await triggerFirstScan(userId)
            if (results) showScanResults(results)
        }
    })
}

function showScanResults(results) {
    document.getElementById('scan-status').classList.add('hidden')
    document.getElementById('scan-results').classList.remove('hidden')
    document.getElementById('scan-results').innerHTML = `
    <div class="results-card success">
      <h3>🎉 Scan Complete!</h3>
      <div class="result-stats">
        <div class="stat">
          <span class="stat-value">${results.total_licenses}</span>
          <span class="stat-label">Total Licenses</span>
        </div>
        <div class="stat ghost">
          <span class="stat-value">${results.ghost_licenses}</span>
          <span class="stat-label">Ghost Licenses</span>
        </div>
        <div class="stat savings">
          <span class="stat-value">$${results.potential_savings.toLocaleString()}</span>
          <span class="stat-label">Potential Annual Savings</span>
        </div>
      </div>
      <a href="/dashboard" class="btn btn-primary">Go to Dashboard →</a>
    </div>
  `
}

export default { initOnboardingPage }
