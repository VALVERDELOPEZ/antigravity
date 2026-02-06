/**
 * Gmail API Query Builder for SaaS Invoice Detection
 * Ghost License Reaper - Invoice Scanner Module
 */

// =============================================================================
// TYPES
// =============================================================================

export interface GmailMessage {
    id: string;
    threadId: string;
    labelIds: string[];
    snippet: string;
    payload: {
        headers: Array<{ name: string; value: string }>;
        body?: { data?: string };
        parts?: Array<{
            mimeType: string;
            body: { data?: string };
        }>;
    };
    internalDate: string;
}

export interface GmailListResponse {
    messages: Array<{ id: string; threadId: string }>;
    nextPageToken?: string;
    resultSizeEstimate: number;
}

// =============================================================================
// GMAIL SEARCH QUERY
// =============================================================================

/**
 * Optimized Gmail search query for SaaS invoices
 * Targets: invoices, receipts, billing confirmations
 * Excludes: newsletters, promotions, spam
 * Timeframe: Last 12 months
 */
export const INVOICE_SEARCH_QUERY = [
    // Subject-based patterns
    '(subject:(invoice OR receipt OR "payment received" OR "payment confirmation"',
    'OR "billing statement" OR "subscription renewed" OR "your receipt"',
    'OR "payment successful" OR "charge receipt" OR factura OR recibo))',

    // OR sender-based patterns
    'OR (from:(billing@ OR receipts@ OR invoices@ OR payments@ OR noreply@',
    'OR accounting@ OR orders@ OR subscriptions@))',

    // Exclusions for cleaner results
    '-category:promotions',
    '-category:social',
    '-category:forums',
    '-is:spam',
    '-subject:("unsubscribe" OR "newsletter" OR "weekly digest")',

    // Time constraint
    'newer_than:12m'
].join(' ');

// =============================================================================
// TOP 20 SAAS VENDOR PATTERNS
// =============================================================================

export interface VendorPattern {
    vendor: string;
    senderPatterns: string[];
    subjectPatterns: RegExp[];
    domainHint: string;
    frequency: 'monthly' | 'annual' | 'per-transaction' | 'variable';
}

export const SAAS_VENDORS: VendorPattern[] = [
    {
        vendor: 'Stripe',
        senderPatterns: ['receipts@stripe.com', 'billing@stripe.com'],
        subjectPatterns: [/your receipt from/i, /invoice for/i, /payment to/i],
        domainHint: 'stripe.com',
        frequency: 'per-transaction'
    },
    {
        vendor: 'Slack',
        senderPatterns: ['feedback@slack.com', 'billing@slack.com'],
        subjectPatterns: [/slack invoice/i, /slack receipt/i, /slack subscription/i],
        domainHint: 'slack.com',
        frequency: 'monthly'
    },
    {
        vendor: 'Notion',
        senderPatterns: ['team@makenotion.com', 'billing@notion.so'],
        subjectPatterns: [/notion receipt/i, /notion invoice/i, /notion subscription/i],
        domainHint: 'notion.so',
        frequency: 'monthly'
    },
    {
        vendor: 'GitHub',
        senderPatterns: ['noreply@github.com', 'billing@github.com'],
        subjectPatterns: [/payment receipt/i, /github invoice/i, /billing statement/i],
        domainHint: 'github.com',
        frequency: 'monthly'
    },
    {
        vendor: 'Figma',
        senderPatterns: ['billing@figma.com', 'noreply@figma.com'],
        subjectPatterns: [/figma invoice/i, /figma receipt/i, /payment confirmed/i],
        domainHint: 'figma.com',
        frequency: 'monthly'
    },
    {
        vendor: 'AWS',
        senderPatterns: ['aws-receivables@amazon.com', 'no-reply@amazon.com'],
        subjectPatterns: [/amazon web services invoice/i, /aws invoice/i, /billing statement/i],
        domainHint: 'amazon.com',
        frequency: 'monthly'
    },
    {
        vendor: 'Google Workspace',
        senderPatterns: ['payments-noreply@google.com', 'googleworkspace-noreply@google.com'],
        subjectPatterns: [/google receipt/i, /google workspace/i, /google cloud/i],
        domainHint: 'google.com',
        frequency: 'monthly'
    },
    {
        vendor: 'Atlassian',
        senderPatterns: ['noreply@atlassian.com', 'billing@atlassian.com'],
        subjectPatterns: [/atlassian invoice/i, /jira receipt/i, /confluence billing/i],
        domainHint: 'atlassian.com',
        frequency: 'monthly'
    },
    {
        vendor: 'Zoom',
        senderPatterns: ['no-reply@zoom.us', 'billing@zoom.us'],
        subjectPatterns: [/zoom receipt/i, /zoom invoice/i, /zoom subscription/i],
        domainHint: 'zoom.us',
        frequency: 'monthly'
    },
    {
        vendor: 'Dropbox',
        senderPatterns: ['no-reply@dropbox.com', 'billing@dropbox.com'],
        subjectPatterns: [/dropbox receipt/i, /dropbox invoice/i, /payment received/i],
        domainHint: 'dropbox.com',
        frequency: 'monthly'
    },
    {
        vendor: 'HubSpot',
        senderPatterns: ['billing@hubspot.com', 'noreply@hubspot.com'],
        subjectPatterns: [/hubspot invoice/i, /hubspot receipt/i, /subscription/i],
        domainHint: 'hubspot.com',
        frequency: 'monthly'
    },
    {
        vendor: 'Intercom',
        senderPatterns: ['receipts@intercom.io', 'billing@intercom.com'],
        subjectPatterns: [/intercom receipt/i, /intercom invoice/i, /payment/i],
        domainHint: 'intercom.io',
        frequency: 'monthly'
    },
    {
        vendor: 'Mailchimp',
        senderPatterns: ['billing@mailchimp.com', 'noreply@mailchimp.com'],
        subjectPatterns: [/mailchimp receipt/i, /mailchimp invoice/i, /intuit/i],
        domainHint: 'mailchimp.com',
        frequency: 'monthly'
    },
    {
        vendor: 'Salesforce',
        senderPatterns: ['billing@salesforce.com', 'noreply@salesforce.com'],
        subjectPatterns: [/salesforce invoice/i, /salesforce receipt/i, /renewal/i],
        domainHint: 'salesforce.com',
        frequency: 'annual'
    },
    {
        vendor: 'Vercel',
        senderPatterns: ['billing@vercel.com', 'noreply@vercel.com'],
        subjectPatterns: [/vercel invoice/i, /vercel receipt/i, /payment/i],
        domainHint: 'vercel.com',
        frequency: 'monthly'
    },
    {
        vendor: 'MongoDB',
        senderPatterns: ['billing@mongodb.com', 'noreply@mongodb.com'],
        subjectPatterns: [/mongodb atlas invoice/i, /mongodb receipt/i, /atlas billing/i],
        domainHint: 'mongodb.com',
        frequency: 'monthly'
    },
    {
        vendor: 'Twilio',
        senderPatterns: ['billing@twilio.com', 'noreply@twilio.com'],
        subjectPatterns: [/twilio invoice/i, /twilio receipt/i, /usage statement/i],
        domainHint: 'twilio.com',
        frequency: 'monthly'
    },
    {
        vendor: 'Heroku',
        senderPatterns: ['billing@heroku.com', 'noreply@heroku.com'],
        subjectPatterns: [/heroku invoice/i, /heroku receipt/i, /dyno billing/i],
        domainHint: 'heroku.com',
        frequency: 'monthly'
    },
    {
        vendor: 'Linear',
        senderPatterns: ['receipts@linear.app', 'billing@linear.app'],
        subjectPatterns: [/linear receipt/i, /linear invoice/i, /subscription/i],
        domainHint: 'linear.app',
        frequency: 'monthly'
    },
    {
        vendor: '1Password',
        senderPatterns: ['billing@1password.com', 'noreply@1password.com'],
        subjectPatterns: [/1password receipt/i, /1password invoice/i, /renewal/i],
        domainHint: '1password.com',
        frequency: 'annual'
    }
];

// =============================================================================
// GMAIL API HELPERS
// =============================================================================

const GMAIL_API_BASE = 'https://gmail.googleapis.com/gmail/v1/users/me';

/**
 * Fetch emails matching invoice query with pagination
 */
export async function fetchInvoiceEmails(
    accessToken: string,
    pageToken?: string,
    maxResults = 50
): Promise<GmailListResponse> {
    const params = new URLSearchParams({
        q: INVOICE_SEARCH_QUERY,
        maxResults: maxResults.toString(),
    });

    if (pageToken) {
        params.set('pageToken', pageToken);
    }

    const response = await fetch(`${GMAIL_API_BASE}/messages?${params}`, {
        headers: {
            'Authorization': `Bearer ${accessToken}`,
            'Content-Type': 'application/json',
        },
    });

    if (!response.ok) {
        const error = await response.text();
        throw new Error(`Gmail API error: ${response.status} - ${error}`);
    }

    return response.json();
}

/**
 * Get full email message by ID
 */
export async function getEmailMessage(
    accessToken: string,
    messageId: string
): Promise<GmailMessage> {
    const response = await fetch(
        `${GMAIL_API_BASE}/messages/${messageId}?format=full`,
        {
            headers: {
                'Authorization': `Bearer ${accessToken}`,
                'Content-Type': 'application/json',
            },
        }
    );

    if (!response.ok) {
        const error = await response.text();
        throw new Error(`Gmail API error fetching message ${messageId}: ${response.status} - ${error}`);
    }

    return response.json();
}

/**
 * Extract header value from Gmail message
 */
export function getHeader(message: GmailMessage, name: string): string | undefined {
    const header = message.payload.headers.find(
        (h) => h.name.toLowerCase() === name.toLowerCase()
    );
    return header?.value;
}

/**
 * Decode base64url encoded content
 */
export function decodeBase64Url(data: string): string {
    // Replace URL-safe characters back to standard base64
    const base64 = data.replace(/-/g, '+').replace(/_/g, '/');
    // Decode using built-in atob
    try {
        return decodeURIComponent(
            atob(base64)
                .split('')
                .map((c) => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2))
                .join('')
        );
    } catch {
        // Fallback for non-UTF8 content
        return atob(base64);
    }
}

/**
 * Extract email body content (prefers plain text, falls back to HTML)
 */
export function extractEmailBody(message: GmailMessage): string {
    // Try to get plain text body from parts
    if (message.payload.parts) {
        const textPart = message.payload.parts.find(
            (p) => p.mimeType === 'text/plain' && p.body.data
        );
        if (textPart?.body.data) {
            return decodeBase64Url(textPart.body.data);
        }

        // Fallback to HTML
        const htmlPart = message.payload.parts.find(
            (p) => p.mimeType === 'text/html' && p.body.data
        );
        if (htmlPart?.body.data) {
            const html = decodeBase64Url(htmlPart.body.data);
            // Strip HTML tags for text extraction
            return html.replace(/<[^>]*>/g, ' ').replace(/\s+/g, ' ').trim();
        }
    }

    // Try direct body
    if (message.payload.body?.data) {
        return decodeBase64Url(message.payload.body.data);
    }

    // Last resort: use snippet
    return message.snippet || '';
}

/**
 * Rate limiting helper with exponential backoff
 */
export async function withRetry<T>(
    fn: () => Promise<T>,
    maxRetries = 3,
    baseDelay = 1000
): Promise<T> {
    let lastError: Error | undefined;

    for (let attempt = 0; attempt < maxRetries; attempt++) {
        try {
            return await fn();
        } catch (error) {
            lastError = error as Error;

            // Check if rate limited
            if (lastError.message.includes('429') || lastError.message.includes('quota')) {
                const delay = baseDelay * Math.pow(2, attempt);
                console.log(`Rate limited, retrying in ${delay}ms...`);
                await new Promise((resolve) => setTimeout(resolve, delay));
            } else {
                throw error;
            }
        }
    }

    throw lastError;
}
