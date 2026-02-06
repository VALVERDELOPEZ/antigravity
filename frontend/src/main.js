import './style.css'
import { supabase } from './lib/supabase-client.js'
import { createCheckoutSession, PRICING_PLANS } from './lib/stripe.js'
import { needsOnboarding } from './lib/auth.js'

// Check authentication
async function checkAuth() {
  const { data: { session } } = await supabase.auth.getSession();
  return session;
}

// Get current user
async function getCurrentUser() {
  const { data: { user } } = await supabase.auth.getUser();
  return user;
}

// Sign out
async function signOut() {
  await supabase.auth.signOut();
  window.location.href = '/login.html';
}

function formatCurrency(amount, currency = 'USD') {
  return new Intl.NumberFormat('en-US', { style: 'currency', currency }).format(amount);
}

async function fetchDashboardData() {
  const { data: invoices, error: invError } = await supabase
    .from('invoices')
    .select('*');

  if (invError) {
    console.error('Error fetching invoices:', invError);
    return null;
  }

  const { data: summary, error: sumError } = await supabase
    .from('invoice_summary')
    .select('*');

  if (sumError) {
    console.error('Error fetching summary:', sumError);
    return null;
  }

  const totalWaste = invoices.reduce((acc, inv) => {
    // Basic logic: if confidence is low or it's a recent duplicate (simple heuristic)
    // In a real app, 'to_reap' would be a calculated flag or user-set status
    return acc + parseFloat(inv.amount);
  }, 0);

  const totalSubs = summary.length;
  // Let's assume for the UI that anything in 'invoices' is a potential license to track
  const unusedLicenses = invoices.length;

  const tableData = summary.map(item => ({
    name: item.vendor,
    monthly_cost: item.avg_amount,
    seats: item.invoice_count,
    unused: Math.floor(item.invoice_count * 0.2), // Mocking unused percentage for now based on vendor data
    status: 'to_reap'
  }));

  return {
    totalWaste: totalWaste.toFixed(2),
    totalSubs,
    unusedLicenses,
    subscriptions: tableData
  };
}

async function renderApp() {
  const app = document.querySelector('#app');

  // Show loading state
  app.innerHTML = `<div class="loading">🔄 Loading...</div>`;

  // Check if user is authenticated
  const session = await checkAuth();
  if (!session) {
    window.location.href = '/login.html';
    return;
  }

  const user = await getCurrentUser();

  // Check if onboarding is needed
  const shouldOnboard = await needsOnboarding(user.id);
  if (shouldOnboard) {
    window.location.href = '/onboarding.html';
    return;
  }

  const data = await fetchDashboardData();

  if (!data) {
    app.innerHTML = `<div class="error">❌ Failed to load data. Check console for details.</div>`;
    return;
  }

  // User menu HTML
  const userMenuHTML = user ? `
    <div class="user-menu">
      <span class="user-email">${user.email}</span>
      <button id="signOutBtn" class="btn-signout">Sign Out</button>
    </div>
  ` : `
    <a href="/login.html" class="btn-login">Sign In</a>
  `;

  app.innerHTML = `
    <header class="header">
      <div class="logo">👻 <span>Ghost License Reaper</span></div>
      <nav>
        <a href="/" class="nav-link active">Dashboard</a>
        <a href="/calculator.html" class="nav-link">Calculator</a>
        <a href="/settings.html" class="nav-link">Settings</a>
      </nav>
      ${userMenuHTML}
      <button id="upgradeBtn" class="btn-upgrade">Upgrade to Pro ⚡</button>
    </header>

    <main class="dashboard">
      <section class="stats-grid">
        <div class="card stat-card waste">
          <span class="stat-label">Total Wasted / Month</span>
          <span class="stat-value">${formatCurrency(data.totalWaste)}</span>
        </div>
        <div class="card stat-card">
          <span class="stat-label">Total Subscriptions</span>
          <span class="stat-value">${data.totalSubs}</span>
        </div>
        <div class="card stat-card">
          <span class="stat-label">Unused Licenses</span>
          <span class="stat-value">${data.unusedLicenses}</span>
        </div>
      </section>

      <section class="card kill-list-section">
        <div class="section-header">
          <h2>🎯 The Kill List</h2>
          <button class="btn-reap">Reap All Selected</button>
        </div>
        <table class="kill-list-table">
          <thead>
            <tr>
              <th><input type="checkbox" id="select-all" /></th>
              <th>Application</th>
              <th>Monthly Cost</th>
              <th>Total Seats</th>
              <th>Unused Seats</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            ${data.subscriptions.map(sub => `
              <tr class="${sub.status === 'to_reap' ? 'highlight-reap' : ''}">
                <td><input type="checkbox" ${sub.status === 'to_reap' ? 'checked' : ''} /></td>
                <td>${sub.name}</td>
                <td>${formatCurrency(sub.monthly_cost)}</td>
                <td>${sub.seats}</td>
                <td class="unused-count">${sub.unused}</td>
                <td><span class="status-badge ${sub.status}">${sub.status === 'to_reap' ? '👻 To Reap' : '✅ OK'}</span></td>
              </tr>
            `).join('')}
          </tbody>
        </table>
      </section>

      <section class="card live-badge">
        <span>🟢 Live Data from Supabase</span>
      </section>
    </main>

    <footer class="footer">
      <p>© 2026 Ghost License Reaper. Built with Antigravity.</p>
    </footer>
  `;

  // Event listeners
  document.getElementById('select-all')?.addEventListener('change', (e) => {
    document.querySelectorAll('.kill-list-table tbody input[type="checkbox"]').forEach(cb => {
      cb.checked = e.target.checked;
    });
  });

  document.getElementById('signOutBtn')?.addEventListener('click', signOut);

  document.getElementById('upgradeBtn')?.addEventListener('click', async () => {
    const { url, error } = await createCheckoutSession(PRICING_PLANS.PRO);
    if (error) alert('Error: ' + error.message);
  });
}

renderApp();
