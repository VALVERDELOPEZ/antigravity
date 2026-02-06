/**
 * Auth Callback Handler
 * Ghost License Reaper - Handles OAuth/Magic Link redirects
 */

import { handleAuthCallback, needsOnboarding, getUser } from '../lib/auth.js'

export const initAuthCallback = async () => {
    const container = document.getElementById('callback-status')

    try {
        container.innerHTML = '<div class="loading">🔄 Completing sign in...</div>'

        const { session, error } = await handleAuthCallback()

        if (error) throw error

        if (session) {
            container.innerHTML = '<div class="success">✅ Signed in successfully!</div>'

            // Check if user needs onboarding
            const { user } = await getUser()
            const requiresOnboarding = await needsOnboarding(user.id)

            // Redirect after short delay
            setTimeout(() => {
                window.location.href = requiresOnboarding ? '/onboarding' : '/dashboard'
            }, 1000)
        } else {
            container.innerHTML = '<div class="error">❌ No session found. <a href="/login">Try again</a></div>'
        }
    } catch (error) {
        console.error('Auth callback error:', error)
        container.innerHTML = `<div class="error">❌ ${error.message} <a href="/login">Try again</a></div>`
    }
}

export default { initAuthCallback }
