/**
 * Supabase Edge Function: Gmail Invoice Scanner
 * Ghost License Reaper - Main Handler
 * 
 * Scans user's Gmail inbox for SaaS invoices and saves to database
 */

import { serve } from 'https://deno.land/std@0.168.0/http/server.ts';
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2';
import {
    fetchInvoiceEmails,
    getEmailMessage,
    getHeader,
    extractEmailBody,
    withRetry,
    type GmailMessage,
} from './gmail-query.ts';
import { extractInvoiceData, type ExtractedInvoice } from './extractors.ts';

// =============================================================================
// TYPES
// =============================================================================

interface ScanRequest {
    accessToken: string;   // Gmail OAuth access token
    maxEmails?: number;    // Maximum emails to process (default: 100)
    fullScan?: boolean;    // Process all pages (default: false)
}

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

interface InvoiceInsert {
    user_id: string;
    vendor: string;
    amount: number;
    currency: string;
    invoice_date: string;
    renewal_date: string | null;
    invoice_id: string | null;
    email_id: string;
    raw_subject: string;
    confidence_score: number;
}

// =============================================================================
// CORS HEADERS
// =============================================================================

const corsHeaders = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
};

// =============================================================================
// MAIN HANDLER
// =============================================================================

serve(async (req) => {
    // Handle CORS preflight
    if (req.method === 'OPTIONS') {
        return new Response('ok', { headers: corsHeaders });
    }

    try {
        // Initialize Supabase client with service role for database operations
        const supabaseUrl = Deno.env.get('SUPABASE_URL')!;
        const supabaseServiceKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!;
        const supabase = createClient(supabaseUrl, supabaseServiceKey);

        // Get authenticated user from JWT
        const authHeader = req.headers.get('Authorization');
        if (!authHeader) {
            return new Response(
                JSON.stringify({ error: 'Missing authorization header' }),
                { status: 401, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
            );
        }

        // Verify JWT and get user
        const token = authHeader.replace('Bearer ', '');
        const { data: { user }, error: authError } = await supabase.auth.getUser(token);

        if (authError || !user) {
            return new Response(
                JSON.stringify({ error: 'Unauthorized', details: authError?.message }),
                { status: 401, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
            );
        }

        // Parse request body
        const body: ScanRequest = await req.json();

        if (!body.accessToken) {
            return new Response(
                JSON.stringify({ error: 'Missing Gmail access token' }),
                { status: 400, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
            );
        }

        const maxEmails = body.maxEmails || 100;
        const fullScan = body.fullScan || false;

        console.log(`[Invoice Scanner] Starting scan for user ${user.id}, maxEmails: ${maxEmails}`);

        // ==========================================================================
        // STEP 1: Fetch email list from Gmail
        // ==========================================================================

        const emailIds: string[] = [];
        let pageToken: string | undefined;
        let totalFetched = 0;

        do {
            const listResponse = await withRetry(() =>
                fetchInvoiceEmails(body.accessToken, pageToken, 50)
            );

            if (listResponse.messages) {
                for (const msg of listResponse.messages) {
                    emailIds.push(msg.id);
                    totalFetched++;

                    if (totalFetched >= maxEmails) break;
                }
            }

            pageToken = fullScan ? listResponse.nextPageToken : undefined;

        } while (pageToken && totalFetched < maxEmails);

        console.log(`[Invoice Scanner] Found ${emailIds.length} potential invoice emails`);

        // ==========================================================================
        // STEP 2: Check which emails we've already processed
        // ==========================================================================

        const { data: existingInvoices } = await supabase
            .from('invoices')
            .select('email_id')
            .eq('user_id', user.id)
            .in('email_id', emailIds);

        const processedEmailIds = new Set(
            existingInvoices?.map((inv) => inv.email_id) || []
        );

        const newEmailIds = emailIds.filter((id) => !processedEmailIds.has(id));

        console.log(`[Invoice Scanner] ${newEmailIds.length} new emails to process (${processedEmailIds.size} already in database)`);

        // ==========================================================================
        // STEP 3: Process each new email
        // ==========================================================================

        const result: ScanResult = {
            success: true,
            processed: 0,
            saved: 0,
            skipped: 0,
            errors: [],
            invoices: [],
        };

        const invoicesToInsert: InvoiceInsert[] = [];

        for (const emailId of newEmailIds) {
            try {
                // Fetch full email message
                const message: GmailMessage = await withRetry(() =>
                    getEmailMessage(body.accessToken, emailId)
                );

                // Extract email metadata
                const from = getHeader(message, 'From') || '';
                const subject = getHeader(message, 'Subject') || '';
                const dateStr = getHeader(message, 'Date') || '';
                const emailDate = dateStr ? new Date(dateStr) : new Date();

                // Extract body content
                const body = extractEmailBody(message);

                // Run extraction
                const extraction = extractInvoiceData(from, subject, body, emailDate);

                result.processed++;

                if (!extraction.success || !extraction.data) {
                    result.skipped++;
                    if (extraction.errors.length > 0) {
                        console.log(`[Invoice Scanner] Skipped ${emailId}: ${extraction.errors.join(', ')}`);
                    }
                    continue;
                }

                const invoice = extraction.data;

                // Prepare for database insertion
                invoicesToInsert.push({
                    user_id: user.id,
                    vendor: invoice.vendor,
                    amount: invoice.amount,
                    currency: invoice.currency,
                    invoice_date: invoice.invoiceDate.toISOString().split('T')[0],
                    renewal_date: invoice.renewalDate?.toISOString().split('T')[0] || null,
                    invoice_id: invoice.invoiceId,
                    email_id: emailId,
                    raw_subject: subject.substring(0, 255),
                    confidence_score: invoice.confidenceScore,
                });

                result.invoices.push({
                    vendor: invoice.vendor,
                    amount: invoice.amount,
                    currency: invoice.currency,
                    invoiceDate: invoice.invoiceDate.toISOString().split('T')[0],
                });

                // Add small delay to avoid rate limiting
                await new Promise((resolve) => setTimeout(resolve, 100));

            } catch (error) {
                const errorMsg = error instanceof Error ? error.message : 'Unknown error';
                result.errors.push(`Email ${emailId}: ${errorMsg}`);
                console.error(`[Invoice Scanner] Error processing ${emailId}:`, errorMsg);
            }
        }

        // ==========================================================================
        // STEP 4: Batch insert invoices into database
        // ==========================================================================

        if (invoicesToInsert.length > 0) {
            // Use upsert to handle any edge cases of duplicate email_ids
            const { data: insertedData, error: insertError } = await supabase
                .from('invoices')
                .upsert(invoicesToInsert, {
                    onConflict: 'email_id',
                    ignoreDuplicates: true,
                })
                .select();

            if (insertError) {
                console.error('[Invoice Scanner] Database insert error:', insertError);
                result.errors.push(`Database error: ${insertError.message}`);
            } else {
                result.saved = insertedData?.length || invoicesToInsert.length;
                console.log(`[Invoice Scanner] Saved ${result.saved} invoices to database`);
            }
        }

        // ==========================================================================
        // STEP 5: Update user's last scan timestamp
        // ==========================================================================

        await supabase
            .from('user_profiles')
            .upsert({
                user_id: user.id,
                last_invoice_scan: new Date().toISOString(),
            }, {
                onConflict: 'user_id',
            });

        // ==========================================================================
        // RETURN RESULTS
        // ==========================================================================

        console.log(`[Invoice Scanner] Scan complete. Processed: ${result.processed}, Saved: ${result.saved}, Skipped: ${result.skipped}`);

        return new Response(
            JSON.stringify(result),
            {
                status: 200,
                headers: { ...corsHeaders, 'Content-Type': 'application/json' },
            }
        );

    } catch (error) {
        console.error('[Invoice Scanner] Fatal error:', error);

        return new Response(
            JSON.stringify({
                success: false,
                error: error instanceof Error ? error.message : 'Internal server error',
            }),
            {
                status: 500,
                headers: { ...corsHeaders, 'Content-Type': 'application/json' },
            }
        );
    }
});
