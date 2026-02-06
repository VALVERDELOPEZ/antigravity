/**
 * Supabase Edge Function: Outreach Reply Detector
 * Ghost License Reaper - Autonomous Outreach Module
 * 
 * Scans the user's Gmail for replies to outreach emails sent by the IA.
 */

import { serve } from 'https://deno.land/std@0.168.0/http/server.ts';
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2';
import {
    withRetry,
    getEmailMessage,
    getHeader,
    extractEmailBody,
} from '../scan-invoices/gmail-query.ts';

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
        const supabaseUrl = Deno.env.get('SUPABASE_URL')!;
        const supabaseServiceKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!;
        const supabase = createClient(supabaseUrl, supabaseServiceKey);

        const authHeader = req.headers.get('Authorization');
        if (!authHeader) {
            return new Response(JSON.stringify({ error: 'Missing authHeader' }), { status: 401, headers: corsHeaders });
        }

        const token = authHeader.replace('Bearer ', '');
        const { data: { user }, error: authError } = await supabase.auth.getUser(token);

        if (authError || !user) {
            return new Response(JSON.stringify({ error: 'Unauthorized' }), { status: 401, headers: corsHeaders });
        }

        const { accessToken } = await req.json();
        if (!accessToken) {
            return new Response(JSON.stringify({ error: 'Missing accessToken' }), { status: 400, headers: corsHeaders });
        }

        // 1. Get all leads in 'contacted' status for this user
        // Note: For simplicity, we match by the email address in the 'To' field of our outbound emails
        const { data: contactedLeads, error: leadsError } = await supabase
            .from('leads')
            .select('id, email, username, subject')
            .eq('user_id', user.id)
            .eq('status', 'contacted');

        if (leadsError || !contactedLeads || contactedLeads.length === 0) {
            return new Response(JSON.stringify({ success: true, replied: 0, message: 'No contacted leads found' }), {
                headers: { ...corsHeaders, 'Content-Type': 'application/json' }
            });
        }

        let totalReplied = 0;
        const leadEmails = contactedLeads.map(l => l.email).filter(Boolean);

        // 2. Search Gmail for threads involving these emails where the last message is from THEM
        // Query pattern: from:(email1 OR email2 OR ...)
        const batchSize = 10;
        for (let i = 0; i < leadEmails.length; i += batchSize) {
            const batch = leadEmails.slice(i, i + batchSize);
            const query = `from:(${batch.join(' OR ')})`;

            const listResponse = await withRetry(() =>
                fetch(`https://gmail.googleapis.com/gmail/v1/users/me/messages?q=${encodeURIComponent(query)}&maxResults=20`, {
                    headers: { 'Authorization': `Bearer ${accessToken}` }
                }).then(r => r.json())
            );

            if (listResponse.messages) {
                for (const msgObj of listResponse.messages) {
                    const message = await withRetry(() => getEmailMessage(accessToken, msgObj.id));
                    const from = getHeader(message, 'From');

                    // Match 'from' with our lead list
                    const matchingLead = contactedLeads.find(l => from && from.includes(l.email));

                    if (matchingLead) {
                        // Mark as replied in database
                        await supabase
                            .from('leads')
                            .update({
                                status: 'responded',
                                email_replied: true,
                                email_replied_at: new Date().toISOString(),
                                last_reply_body: extractEmailBody(message)
                            })
                            .eq('id', matchingLead.id);

                        totalReplied++;
                        console.log(`[Reply Detector] Detected reply from ${matchingLead.email} for lead ${matchingLead.id}`);
                    }
                }
            }
        }

        return new Response(JSON.stringify({ success: true, replied: totalReplied }), {
            headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        });

    } catch (error) {
        console.error('[Reply Detector] Error:', error);
        return new Response(JSON.stringify({ error: error.message }), { status: 500, headers: corsHeaders });
    }
});
