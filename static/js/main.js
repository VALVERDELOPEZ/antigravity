/**
 * Lead Finder AI - Main JavaScript
 */

// DOM Ready
document.addEventListener('DOMContentLoaded', function () {
    initMobileMenu();
    initFAQ();
    initAlerts();
    initModals();
});

/**
 * Mobile Menu Toggle
 */
function initMobileMenu() {
    const toggle = document.getElementById('mobileMenuToggle');
    const sidebar = document.querySelector('.sidebar');

    if (toggle && sidebar) {
        toggle.addEventListener('click', () => {
            sidebar.classList.toggle('active');
        });

        // Close on click outside
        document.addEventListener('click', (e) => {
            if (!sidebar.contains(e.target) && !toggle.contains(e.target)) {
                sidebar.classList.remove('active');
            }
        });
    }
}

/**
 * FAQ Accordion
 */
function initFAQ() {
    const faqItems = document.querySelectorAll('.faq-item');

    faqItems.forEach(item => {
        const question = item.querySelector('.faq-question');
        if (question) {
            question.addEventListener('click', () => {
                // Close other items
                faqItems.forEach(other => {
                    if (other !== item) {
                        other.classList.remove('active');
                    }
                });
                // Toggle current
                item.classList.toggle('active');
            });
        }
    });
}

/**
 * Auto-dismiss alerts
 */
function initAlerts() {
    const alerts = document.querySelectorAll('.alert');

    alerts.forEach(alert => {
        setTimeout(() => {
            alert.style.opacity = '0';
            setTimeout(() => alert.remove(), 300);
        }, 5000);
    });
}

/**
 * Modal functionality
 */
function initModals() {
    // Close modal on background click
    document.querySelectorAll('.modal').forEach(modal => {
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                modal.classList.remove('active');
            }
        });
    });

    // Close on Escape key
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            document.querySelectorAll('.modal.active').forEach(modal => {
                modal.classList.remove('active');
            });
        }
    });
}

/**
 * Utility: Debounce function
 */
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

/**
 * Utility: Format number with commas
 */
function formatNumber(num) {
    return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ',');
}

/**
 * Utility: API Request helper
 */
async function apiRequest(url, options = {}) {
    const defaultOptions = {
        headers: {
            'Content-Type': 'application/json'
        }
    };

    const response = await fetch(url, { ...defaultOptions, ...options });
    const data = await response.json();

    if (!response.ok) {
        throw new Error(data.message || 'API request failed');
    }

    return data;
}

/**
 * Refresh dashboard stats
 */
async function refreshStats() {
    try {
        const data = await apiRequest('/api/stats');
        if (data.success) {
            // Update stat cards
            document.querySelectorAll('.stat-value').forEach((el, index) => {
                const values = [
                    data.data.total_leads,
                    data.data.high_score_leads,
                    data.data.emails_sent,
                    data.data.conversion_rate + '%'
                ];
                if (values[index] !== undefined) {
                    el.textContent = values[index];
                }
            });
        }
    } catch (error) {
        console.error('Failed to refresh stats:', error);
    }
}

/**
 * Send email to lead
 */
async function sendEmail(leadId) {
    if (!confirm('Send AI-generated email to this lead?')) return;

    try {
        const data = await apiRequest('/api/send-email', {
            method: 'POST',
            body: JSON.stringify({ lead_id: leadId })
        });

        alert(data.message || 'Email sent successfully!');
        if (data.success) {
            location.reload();
        }
    } catch (error) {
        alert('Error: ' + error.message);
    }
}

/**
 * Smooth scroll to anchor
 */
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        const href = this.getAttribute('href');
        if (href === '#') return;

        e.preventDefault();
        const target = document.querySelector(href);
        if (target) {
            target.scrollIntoView({
                behavior: 'smooth',
                block: 'start'
            });
        }
    });
});

/**
 * Add loading state to buttons
 */
document.querySelectorAll('form').forEach(form => {
    form.addEventListener('submit', function () {
        const btn = form.querySelector('button[type="submit"]');
        if (btn && !btn.disabled) {
            btn.disabled = true;
            const originalText = btn.innerHTML;
            btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Loading...';

            // Re-enable after timeout (in case of error)
            setTimeout(() => {
                btn.disabled = false;
                btn.innerHTML = originalText;
            }, 10000);
        }
    });
});

console.log('Lead Finder AI initialized');
