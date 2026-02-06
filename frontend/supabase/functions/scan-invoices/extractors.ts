/**
 * Invoice Data Extractors
 * Ghost License Reaper - Pattern Matching & Data Extraction
 */

import { SAAS_VENDORS, type VendorPattern } from './gmail-query.ts';

// =============================================================================
// TYPES
// =============================================================================

export interface ExtractedInvoice {
    vendor: string;
    amount: number;
    currency: string;
    invoiceDate: Date;
    renewalDate: Date | null;
    invoiceId: string | null;
    confidenceScore: number;
}

export interface ExtractionResult {
    success: boolean;
    data: ExtractedInvoice | null;
    errors: string[];
}

// =============================================================================
// CURRENCY PATTERNS
// =============================================================================

const CURRENCY_SYMBOLS: Record<string, string> = {
    '$': 'USD',
    '€': 'EUR',
    '£': 'GBP',
    '¥': 'JPY',
    '₹': 'INR',
    'A$': 'AUD',
    'C$': 'CAD',
    'CHF': 'CHF',
    'R$': 'BRL',
    'MX$': 'MXN',
};

const CURRENCY_CODES = ['USD', 'EUR', 'GBP', 'JPY', 'INR', 'AUD', 'CAD', 'CHF', 'BRL', 'MXN'];

// =============================================================================
// AMOUNT EXTRACTION
// =============================================================================

/**
 * Regex patterns for extracting monetary amounts
 * Handles: $10.00, 10.00 USD, €50, 1,234.56, etc.
 */
const AMOUNT_PATTERNS = [
    // Symbol before amount: $10.00, €50.00, £100
    /(?<currency>[\$€£¥₹])[\s]*(?<amount>[\d,]+(?:\.\d{2})?)/g,

    // Amount with code after: 10.00 USD, 50 EUR
    /(?<amount>[\d,]+(?:\.\d{2})?)\s*(?<currency>USD|EUR|GBP|JPY|INR|AUD|CAD|CHF|BRL|MXN)/gi,

    // Prefixed amounts: USD 10.00, EUR 50
    /(?<currency>USD|EUR|GBP|JPY|INR|AUD|CAD)\s*[\$€£]?[\s]*(?<amount>[\d,]+(?:\.\d{2})?)/gi,

    // Total/Amount followed by value
    /(?:total|amount|charged?|subtotal|grand total|payment)[:\s]+[\$€£]?[\s]*(?<amount>[\d,]+(?:\.\d{2})?)\s*(?<currency>USD|EUR|GBP)?/gi,
];

export function extractAmount(text: string): { amount: number; currency: string } | null {
    const textLower = text.toLowerCase();

    for (const pattern of AMOUNT_PATTERNS) {
        // Reset regex lastIndex for global patterns
        pattern.lastIndex = 0;

        // Find all matches
        const matches = [...text.matchAll(pattern)];

        for (const match of matches) {
            if (match.groups?.amount) {
                // Parse amount (remove commas)
                const amountStr = match.groups.amount.replace(/,/g, '');
                const amount = parseFloat(amountStr);

                if (isNaN(amount) || amount <= 0 || amount > 1000000) {
                    continue; // Skip invalid amounts
                }

                // Determine currency
                let currency = 'USD'; // Default
                const currencyMatch = match.groups.currency;

                if (currencyMatch) {
                    if (CURRENCY_SYMBOLS[currencyMatch]) {
                        currency = CURRENCY_SYMBOLS[currencyMatch];
                    } else if (CURRENCY_CODES.includes(currencyMatch.toUpperCase())) {
                        currency = currencyMatch.toUpperCase();
                    }
                }

                return { amount, currency };
            }
        }
    }

    return null;
}

// =============================================================================
// DATE EXTRACTION
// =============================================================================

/**
 * Date patterns for various formats
 */
const DATE_PATTERNS = [
    // ISO format: 2025-01-15
    /(?<year>\d{4})-(?<month>\d{2})-(?<day>\d{2})/g,

    // US format: January 15, 2025 or Jan 15, 2025
    /(?<month>January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[,\s]+(?<day>\d{1,2})(?:st|nd|rd|th)?[,\s]+(?<year>\d{4})/gi,

    // EU format: 15 January 2025 or 15/01/2025
    /(?<day>\d{1,2})[\s\/\-](?<month>\d{1,2}|January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[\s\/\-](?<year>\d{4})/gi,

    // MM/DD/YYYY or MM-DD-YYYY
    /(?<month>\d{1,2})[\/\-](?<day>\d{1,2})[\/\-](?<year>\d{4})/g,
];

const MONTH_NAMES: Record<string, number> = {
    january: 1, jan: 1,
    february: 2, feb: 2,
    march: 3, mar: 3,
    april: 4, apr: 4,
    may: 5,
    june: 6, jun: 6,
    july: 7, jul: 7,
    august: 8, aug: 8,
    september: 9, sep: 9,
    october: 10, oct: 10,
    november: 11, nov: 11,
    december: 12, dec: 12,
};

export function extractDate(text: string): Date | null {
    for (const pattern of DATE_PATTERNS) {
        pattern.lastIndex = 0;
        const matches = [...text.matchAll(pattern)];

        for (const match of matches) {
            if (match.groups) {
                let year = parseInt(match.groups.year);
                let month: number;
                let day = parseInt(match.groups.day);

                // Parse month (could be number or name)
                const monthStr = match.groups.month.toLowerCase();
                if (MONTH_NAMES[monthStr] !== undefined) {
                    month = MONTH_NAMES[monthStr];
                } else {
                    month = parseInt(match.groups.month);
                }

                // Validate ranges
                if (year < 2020 || year > 2030) continue;
                if (month < 1 || month > 12) continue;
                if (day < 1 || day > 31) continue;

                // Create and validate date
                const date = new Date(year, month - 1, day);
                if (date.getMonth() !== month - 1) continue; // Invalid date

                return date;
            }
        }
    }

    return null;
}

/**
 * Extract renewal/next billing date
 */
export function extractRenewalDate(text: string): Date | null {
    const renewalKeywords = [
        /next (?:billing|payment|charge)[:\s]+/gi,
        /renews? (?:on|date)[:\s]+/gi,
        /subscription (?:renews?|ends?)[:\s]+/gi,
        /valid (?:until|through)[:\s]+/gi,
        /expires?[:\s]+/gi,
    ];

    for (const keyword of renewalKeywords) {
        keyword.lastIndex = 0;
        const match = text.match(keyword);

        if (match && match.index !== undefined) {
            // Get text after the keyword (next 50 chars)
            const afterKeyword = text.substring(match.index + match[0].length, match.index + match[0].length + 50);
            const date = extractDate(afterKeyword);

            if (date) {
                return date;
            }
        }
    }

    return null;
}

// =============================================================================
// VENDOR DETECTION
// =============================================================================

/**
 * Detect vendor from email sender and content
 */
export function detectVendor(
    fromEmail: string,
    subject: string,
    body: string
): { vendor: string; confidence: number } {
    const fromLower = fromEmail.toLowerCase();
    const subjectLower = subject.toLowerCase();
    const combined = `${subject} ${body}`.toLowerCase();

    let bestMatch: { vendor: string; confidence: number } = {
        vendor: 'Unknown',
        confidence: 0,
    };

    for (const vendorPattern of SAAS_VENDORS) {
        let score = 0;

        // Check sender patterns (high weight)
        for (const sender of vendorPattern.senderPatterns) {
            if (fromLower.includes(sender.toLowerCase())) {
                score += 0.5;
            }
        }

        // Check domain hint in from address
        if (fromLower.includes(vendorPattern.domainHint)) {
            score += 0.3;
        }

        // Check subject patterns
        for (const subjectPattern of vendorPattern.subjectPatterns) {
            if (subjectPattern.test(subjectLower)) {
                score += 0.2;
            }
        }

        // Check vendor name in content
        const vendorRegex = new RegExp(`\\b${vendorPattern.vendor}\\b`, 'i');
        if (vendorRegex.test(combined)) {
            score += 0.1;
        }

        if (score > bestMatch.confidence) {
            bestMatch = {
                vendor: vendorPattern.vendor,
                confidence: Math.min(score, 1.0),
            };
        }
    }

    // If no known vendor matched, try to extract from domain
    if (bestMatch.confidence < 0.3) {
        const domainMatch = fromLower.match(/@([a-z0-9-]+)\./);
        if (domainMatch) {
            const domain = domainMatch[1];
            // Capitalize first letter
            bestMatch.vendor = domain.charAt(0).toUpperCase() + domain.slice(1);
            bestMatch.confidence = 0.4;
        }
    }

    return bestMatch;
}

// =============================================================================
// INVOICE ID EXTRACTION
// =============================================================================

const INVOICE_ID_PATTERNS = [
    /invoice[#:\s]+(?<id>[A-Z0-9\-]{4,20})/gi,
    /receipt[#:\s]+(?<id>[A-Z0-9\-]{4,20})/gi,
    /order[#:\s]+(?<id>[A-Z0-9\-]{4,20})/gi,
    /transaction[#:\s]+(?<id>[A-Z0-9\-]{6,30})/gi,
    /reference[#:\s]+(?<id>[A-Z0-9\-]{4,20})/gi,
    /confirmation[#:\s]+(?<id>[A-Z0-9\-]{4,20})/gi,
];

export function extractInvoiceId(text: string): string | null {
    for (const pattern of INVOICE_ID_PATTERNS) {
        pattern.lastIndex = 0;
        const match = pattern.exec(text);

        if (match?.groups?.id) {
            return match.groups.id.toUpperCase();
        }
    }

    return null;
}

// =============================================================================
// MAIN EXTRACTION FUNCTION
// =============================================================================

/**
 * Extract complete invoice data from email content
 */
export function extractInvoiceData(
    fromEmail: string,
    subject: string,
    body: string,
    emailDate: Date
): ExtractionResult {
    const errors: string[] = [];

    // Combine subject and body for extraction
    const fullText = `${subject}\n${body}`;

    // 1. Detect vendor
    const { vendor, confidence: vendorConfidence } = detectVendor(fromEmail, subject, body);

    // 2. Extract amount
    const amountResult = extractAmount(fullText);
    if (!amountResult) {
        errors.push('Could not extract amount');
    }

    // 3. Extract invoice date (prefer extracted, fallback to email date)
    let invoiceDate = extractDate(fullText);
    if (!invoiceDate) {
        invoiceDate = emailDate;
        errors.push('Using email date as invoice date');
    }

    // 4. Extract renewal date (optional)
    const renewalDate = extractRenewalDate(fullText);

    // 5. Extract invoice ID (optional)
    const invoiceId = extractInvoiceId(fullText);

    // Calculate overall confidence score
    let confidenceScore = vendorConfidence;
    if (amountResult) confidenceScore = (confidenceScore + 1) / 2;
    if (invoiceId) confidenceScore = (confidenceScore + 0.1);
    confidenceScore = Math.min(confidenceScore, 0.99);

    // Require at minimum: vendor and amount
    if (!amountResult) {
        return {
            success: false,
            data: null,
            errors,
        };
    }

    return {
        success: true,
        data: {
            vendor,
            amount: amountResult.amount,
            currency: amountResult.currency,
            invoiceDate,
            renewalDate,
            invoiceId,
            confidenceScore: Math.round(confidenceScore * 100) / 100,
        },
        errors,
    };
}
