/**
 * Client-side usage example for Gmail Invoice Scanner
 * Ghost License Reaper - Frontend Integration
 */

import { createClient } from '@supabase/supabase-js';

// =============================================================================
// CONFIGURATION
// =============================================================================

const SUPABASE_URL = 'YOUR_SUPABASE_URL';
const SUPABASE_ANON_KEY = 'YOUR_SUPABASE_ANON_KEY';

// Google OAuth Client ID (from Google Cloud Console)
const GOOGLE_CLIENT_ID = 'YOUR_GOOGLE_CLIENT_ID';

// Gmail scopes needed
const GMAIL_SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'email',
    'profile',
];

// =============================================================================
// SUPABASE CLIENT
// =============================================================================

const supabase = createClient(SUPABASE_URL, SUPABASE_ANON_KEY);

// =============================================================================
// GOOGLE OAUTH FLOW
// =============================================================================

/**
 * Initialize Google OAuth and get Gmail access token
 * Uses popup-based OAuth flow
 */
async function getGmailAccessToken(): Promise<string> {
    return new Promise((resolve, reject) => {
        // Build OAuth URL
        const authUrl = new URL('https://accounts.google.com/o/oauth2/v2/auth');
        authUrl.searchParams.set('client_id', GOOGLE_CLIENT_ID);
        authUrl.searchParams.set('redirect_uri', `${window.location.origin}/oauth/callback`);
        authUrl.searchParams.set('response_type', 'token');
        authUrl.searchParams.set('scope', GMAIL_SCOPES.join(' '));
        authUrl.searchParams.set('access_type', 'online');
        authUrl.searchParams.set('prompt', 'consent');

        // Open popup
        const popup = window.open(
            authUrl.toString(),
            'Google OAuth',
            'width=500,height=600,scrollbars=yes'
        );

        if (!popup) {
            reject(new Error('Popup blocked. Please allow popups for this site.'));
            return;
        }

        // Listen for OAuth callback
        const handleMessage = (event: MessageEvent) => {
            if (event.origin !== window.location.origin) return;

            if (event.data?.type === 'oauth_callback') {
                window.removeEventListener('message', handleMessage);
                popup.close();

                if (event.data.accessToken) {
                    resolve(event.data.accessToken);
                } else {
                    reject(new Error(event.data.error || 'OAuth failed'));
                }
            }
        };

        window.addEventListener('message', handleMessage);

        // Check if popup was closed without completing OAuth
        const checkClosed = setInterval(() => {
            if (popup.closed) {
                clearInterval(checkClosed);
                window.removeEventListener('message', handleMessage);
                reject(new Error('OAuth cancelled by user'));
            }
        }, 1000);
    });
}

// =============================================================================
// SCAN INVOICES
// =============================================================================

interface ScanResult {
    success: boolean;
    processed: number;
    saved: number;
    skipped: number;
    errors: string[];
    invoices: Array<{
        vendor: string;
        amount: number;
        currency: string;
        invoiceDate: string;
    }>;
}

/**
 * Scan Gmail for invoices and save to database
 */
async function scanGmailInvoices(
    accessToken: string,
    options: { maxEmails?: number; fullScan?: boolean } = {}
): Promise<ScanResult> {
    // Get current user's session token
    const { data: { session } } = await supabase.auth.getSession();

    if (!session) {
        throw new Error('User not authenticated');
    }

    // Call Edge Function
    const response = await fetch(`${SUPABASE_URL}/functions/v1/scan-invoices`, {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${session.access_token}`,
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            accessToken,
            maxEmails: options.maxEmails || 100,
            fullScan: options.fullScan || false,
        }),
    });

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.error || 'Scan failed');
    }

    return response.json();
}

// =============================================================================
// FETCH INVOICES
// =============================================================================

interface Invoice {
    id: string;
    vendor: string;
    amount: number;
    currency: string;
    invoice_date: string;
    renewal_date: string | null;
    invoice_id: string | null;
    confidence_score: number;
    created_at: string;
}

/**
 * Fetch user's invoices from database
 */
async function getInvoices(options: {
    vendor?: string;
    limit?: number;
    offset?: number;
} = {}): Promise<Invoice[]> {
    let query = supabase
        .from('invoices')
        .select('*')
        .order('invoice_date', { ascending: false });

    if (options.vendor) {
        query = query.eq('vendor', options.vendor);
    }

    if (options.limit) {
        query = query.limit(options.limit);
    }

    if (options.offset) {
        query = query.range(options.offset, options.offset + (options.limit || 10) - 1);
    }

    const { data, error } = await query;

    if (error) {
        throw new Error(`Failed to fetch invoices: ${error.message}`);
    }

    return data || [];
}

/**
 * Get spending summary by vendor
 */
async function getSpendingSummary(): Promise<Array<{
    vendor: string;
    currency: string;
    invoice_count: number;
    total_amount: number;
    avg_amount: number;
    next_renewal: string | null;
}>> {
    const { data, error } = await supabase
        .from('invoice_summary')
        .select('*')
        .order('total_amount', { ascending: false });

    if (error) {
        throw new Error(`Failed to fetch summary: ${error.message}`);
    }

    return data || [];
}

// =============================================================================
// UI COMPONENTS (React example)
// =============================================================================

/*
// React Component Example

import { useState } from 'react';

function InvoiceScanner() {
  const [scanning, setScanning] = useState(false);
  const [result, setResult] = useState<ScanResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleScan = async () => {
    setScanning(true);
    setError(null);

    try {
      // Step 1: Get Gmail access token
      const accessToken = await getGmailAccessToken();
      
      // Step 2: Scan emails
      const scanResult = await scanGmailInvoices(accessToken, {
        maxEmails: 100,
        fullScan: false,
      });

      setResult(scanResult);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setScanning(false);
    }
  };

  return (
    <div>
      <button onClick={handleScan} disabled={scanning}>
        {scanning ? 'Scanning...' : 'Scan Gmail for Invoices'}
      </button>

      {error && <div className="error">{error}</div>}

      {result && (
        <div className="results">
          <h3>Scan Complete</h3>
          <p>Processed: {result.processed}</p>
          <p>Saved: {result.saved}</p>
          <p>Skipped: {result.skipped}</p>

          <h4>Found Invoices:</h4>
          <ul>
            {result.invoices.map((inv, i) => (
              <li key={i}>
                {inv.vendor}: {inv.currency} {inv.amount.toFixed(2)} ({inv.invoiceDate})
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
*/

// =============================================================================
// OAUTH CALLBACK PAGE (/oauth/callback.html)
// =============================================================================

/*
<!DOCTYPE html>
<html>
<head>
  <title>OAuth Callback</title>
</head>
<body>
  <p>Processing authentication...</p>
  <script>
    // Extract access token from URL hash
    const hash = window.location.hash.substring(1);
    const params = new URLSearchParams(hash);
    
    if (params.get('access_token')) {
      // Send token back to parent window
      window.opener.postMessage({
        type: 'oauth_callback',
        accessToken: params.get('access_token'),
      }, window.location.origin);
    } else {
      // Send error
      window.opener.postMessage({
        type: 'oauth_callback',
        error: params.get('error') || 'OAuth failed',
      }, window.location.origin);
    }
    
    // Close this window (parent will handle it too)
    setTimeout(() => window.close(), 100);
  </script>
</body>
</html>
*/

// =============================================================================
// EXPORTS
// =============================================================================

export {
    getGmailAccessToken,
    scanGmailInvoices,
    getInvoices,
    getSpendingSummary,
    type Invoice,
    type ScanResult,
};
