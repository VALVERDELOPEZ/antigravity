/**
 * Login Page - Ghost License Reaper
 */

import { signInWithMagicLink, signInWithGoogle, isCorporateEmail } from '../lib/auth.js'

export const initLoginPage = () => {
    const loginForm = document.getElementById('login-form')
    const emailInput = document.getElementById('email')
    const emailError = document.getElementById('email-error')
    const magicLinkBtn = document.getElementById('magic-link-btn')
    const googleBtn = document.getElementById('google-login-btn')
    const successMessage = document.getElementById('magic-link-success')

    loginForm?.addEventListener('submit', async (e) => {
        e.preventDefault()
        const email = emailInput.value.trim()
        if (!email) return showError('Please enter your email')

        setLoading(true)
        const result = await signInWithMagicLink(email)
        setLoading(false)

        if (result.success) {
            loginForm.classList.add('hidden')
            successMessage.classList.remove('hidden')
            document.getElementById('sent-email').textContent = email
        } else {
            showError(result.error?.message || 'Failed to send magic link')
        }
    })

    googleBtn?.addEventListener('click', async () => {
        googleBtn.disabled = true
        const result = await signInWithGoogle()
        if (!result.success) {
            googleBtn.disabled = false
            showError(result.error?.message || 'Google login failed')
        }
    })

    function showError(msg) {
        emailError.textContent = msg
        emailError.classList.remove('hidden')
    }

    function setLoading(loading) {
        magicLinkBtn.disabled = loading
        emailInput.disabled = loading
    }
}
