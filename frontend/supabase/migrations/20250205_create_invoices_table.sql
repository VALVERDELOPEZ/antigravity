-- =============================================================================
-- Ghost License Reaper - Invoices Table Migration
-- Stores detected SaaS invoices from Gmail scanning
-- =============================================================================

-- Create invoices table
CREATE TABLE IF NOT EXISTS invoices (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  
  -- Vendor information
  vendor TEXT NOT NULL,
  
  -- Financial data
  amount DECIMAL(10,2) NOT NULL CHECK (amount > 0),
  currency TEXT NOT NULL DEFAULT 'USD' CHECK (currency ~ '^[A-Z]{3}$'),
  
  -- Dates
  invoice_date DATE NOT NULL,
  renewal_date DATE,
  
  -- Invoice identification
  invoice_id TEXT,
  email_id TEXT UNIQUE NOT NULL,  -- Gmail message ID (prevents duplicates)
  raw_subject TEXT,
  
  -- Extraction metadata
  confidence_score DECIMAL(3,2) DEFAULT 0.5 CHECK (confidence_score >= 0 AND confidence_score <= 1),
  
  -- Timestamps
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Create indexes for common queries
CREATE INDEX IF NOT EXISTS idx_invoices_user_id ON invoices(user_id);
CREATE INDEX IF NOT EXISTS idx_invoices_vendor ON invoices(vendor);
CREATE INDEX IF NOT EXISTS idx_invoices_invoice_date ON invoices(invoice_date DESC);
CREATE INDEX IF NOT EXISTS idx_invoices_user_vendor ON invoices(user_id, vendor);

-- Add RLS policies
ALTER TABLE invoices ENABLE ROW LEVEL SECURITY;

-- Users can only see their own invoices
CREATE POLICY "Users can view own invoices"
  ON invoices
  FOR SELECT
  USING (auth.uid() = user_id);

-- Users can insert their own invoices
CREATE POLICY "Users can insert own invoices"
  ON invoices
  FOR INSERT
  WITH CHECK (auth.uid() = user_id);

-- Users can update their own invoices
CREATE POLICY "Users can update own invoices"
  ON invoices
  FOR UPDATE
  USING (auth.uid() = user_id);

-- Users can delete their own invoices
CREATE POLICY "Users can delete own invoices"
  ON invoices
  FOR DELETE
  USING (auth.uid() = user_id);

-- Create updated_at trigger
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_invoices_updated_at
  BEFORE UPDATE ON invoices
  FOR EACH ROW
  EXECUTE FUNCTION update_updated_at_column();

-- =============================================================================
-- User Profiles Table (for tracking scan status)
-- =============================================================================

CREATE TABLE IF NOT EXISTS user_profiles (
  user_id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
  
  -- Gmail integration
  gmail_connected BOOLEAN DEFAULT false,
  gmail_email TEXT,
  last_invoice_scan TIMESTAMPTZ,
  
  -- Company info
  company_name TEXT,
  
  -- Timestamps
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- RLS for user_profiles
ALTER TABLE user_profiles ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own profile"
  ON user_profiles FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own profile"
  ON user_profiles FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own profile"
  ON user_profiles FOR UPDATE USING (auth.uid() = user_id);

-- Updated_at trigger for user_profiles
CREATE TRIGGER update_user_profiles_updated_at
  BEFORE UPDATE ON user_profiles
  FOR EACH ROW
  EXECUTE FUNCTION update_updated_at_column();

-- =============================================================================
-- Useful Views
-- =============================================================================

-- Monthly spending summary by vendor
CREATE OR REPLACE VIEW invoice_summary AS
SELECT 
  user_id,
  vendor,
  currency,
  COUNT(*) as invoice_count,
  SUM(amount) as total_amount,
  AVG(amount) as avg_amount,
  MIN(invoice_date) as first_invoice,
  MAX(invoice_date) as last_invoice,
  MAX(renewal_date) as next_renewal
FROM invoices
GROUP BY user_id, vendor, currency;

-- Grant access to authenticated users
GRANT SELECT ON invoice_summary TO authenticated;
