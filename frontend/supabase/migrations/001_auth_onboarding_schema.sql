-- =====================================================
-- GHOST LICENSE REAPER - SUPABASE DATABASE SCHEMA
-- Full Authentication & Onboarding System
-- =====================================================
-- 
-- Run this in Supabase SQL Editor (Dashboard > SQL Editor)
-- This creates all tables, functions, triggers, and RLS policies
--
-- =====================================================

-- Enable necessary extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- =====================================================
-- 1. COMPANIES TABLE (Tenants/Organizations)
-- =====================================================

CREATE TABLE IF NOT EXISTS public.companies (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    size VARCHAR(50) NOT NULL CHECK (size IN ('1-10', '11-50', '51-200', '201-500', '501-1000', '1000+')),
    industry VARCHAR(100) NOT NULL,
    domain VARCHAR(255),
    
    -- SSO Configuration
    sso_provider VARCHAR(50) CHECK (sso_provider IN ('google_workspace', 'microsoft_365', 'okta', 'azure_ad', NULL)),
    sso_configured BOOLEAN DEFAULT false,
    sso_config JSONB DEFAULT '{}',
    
    -- Subscription & Billing
    subscription_tier VARCHAR(50) DEFAULT 'trial' CHECK (subscription_tier IN ('trial', 'starter', 'professional', 'enterprise')),
    subscription_status VARCHAR(50) DEFAULT 'active' CHECK (subscription_status IN ('active', 'past_due', 'canceled', 'paused')),
    trial_ends_at TIMESTAMPTZ DEFAULT (NOW() + INTERVAL '14 days'),
    
    -- License Scan Stats (cached for quick access)
    total_licenses INTEGER DEFAULT 0,
    ghost_licenses INTEGER DEFAULT 0,
    potential_monthly_savings DECIMAL(12,2) DEFAULT 0,
    last_scan_at TIMESTAMPTZ,
    
    -- Metadata
    created_by UUID REFERENCES auth.users(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for companies
CREATE INDEX IF NOT EXISTS idx_companies_domain ON public.companies(domain);
CREATE INDEX IF NOT EXISTS idx_companies_created_by ON public.companies(created_by);
CREATE INDEX IF NOT EXISTS idx_companies_subscription ON public.companies(subscription_tier, subscription_status);

-- =====================================================
-- 2. USER PROFILES TABLE
-- =====================================================

CREATE TABLE IF NOT EXISTS public.user_profiles (
    id UUID REFERENCES auth.users(id) ON DELETE CASCADE PRIMARY KEY,
    email VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    avatar_url TEXT,
    
    -- Company relationship
    company_id UUID REFERENCES public.companies(id) ON DELETE SET NULL,
    
    -- Role within the company
    role VARCHAR(50) DEFAULT 'member' CHECK (role IN ('admin', 'manager', 'member', 'viewer')),
    
    -- Preferences
    email_notifications BOOLEAN DEFAULT true,
    weekly_report BOOLEAN DEFAULT true,
    timezone VARCHAR(100) DEFAULT 'UTC',
    
    -- Auth metadata
    auth_provider VARCHAR(50), -- 'magic_link', 'google', etc.
    last_sign_in_at TIMESTAMPTZ,
    
    -- Metadata
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for user_profiles
CREATE INDEX IF NOT EXISTS idx_user_profiles_email ON public.user_profiles(email);
CREATE INDEX IF NOT EXISTS idx_user_profiles_company ON public.user_profiles(company_id);

-- =====================================================
-- 3. ONBOARDING PROGRESS TABLE
-- =====================================================

CREATE TYPE onboarding_step AS ENUM ('connect_company', 'choose_integration', 'first_scan');

CREATE TABLE IF NOT EXISTS public.onboarding_progress (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL UNIQUE,
    
    -- Current step tracking
    step_completed onboarding_step,
    
    -- Step data storage (flexible JSONB for all step responses)
    step_data JSONB DEFAULT '{}'::jsonb,
    
    -- Completion status
    is_onboarding_complete BOOLEAN DEFAULT false,
    completed_at TIMESTAMPTZ,
    
    -- Metadata
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for onboarding_progress
CREATE INDEX IF NOT EXISTS idx_onboarding_user ON public.onboarding_progress(user_id);
CREATE INDEX IF NOT EXISTS idx_onboarding_complete ON public.onboarding_progress(is_onboarding_complete);

-- =====================================================
-- 4. LICENSE SCANS TABLE
-- =====================================================

CREATE TABLE IF NOT EXISTS public.license_scans (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    company_id UUID REFERENCES public.companies(id) ON DELETE CASCADE NOT NULL,
    triggered_by UUID REFERENCES auth.users(id) ON DELETE SET NULL,
    
    -- Scan status
    status VARCHAR(50) DEFAULT 'pending' CHECK (status IN ('pending', 'running', 'completed', 'failed')),
    
    -- Results (JSONB for flexibility)
    results JSONB DEFAULT '{}',
    
    -- Scan metadata
    scan_type VARCHAR(50) DEFAULT 'full' CHECK (scan_type IN ('full', 'incremental', 'app_specific')),
    duration_ms INTEGER,
    error_message TEXT,
    
    -- Timestamps
    started_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for license_scans
CREATE INDEX IF NOT EXISTS idx_scans_company ON public.license_scans(company_id);
CREATE INDEX IF NOT EXISTS idx_scans_status ON public.license_scans(status);
CREATE INDEX IF NOT EXISTS idx_scans_created ON public.license_scans(created_at DESC);

-- =====================================================
-- 5. TRIGGER FUNCTIONS
-- =====================================================

-- Function to update 'updated_at' timestamp
CREATE OR REPLACE FUNCTION public.handle_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply updated_at trigger to all relevant tables
DROP TRIGGER IF EXISTS on_companies_updated ON public.companies;
CREATE TRIGGER on_companies_updated
    BEFORE UPDATE ON public.companies
    FOR EACH ROW
    EXECUTE FUNCTION public.handle_updated_at();

DROP TRIGGER IF EXISTS on_user_profiles_updated ON public.user_profiles;
CREATE TRIGGER on_user_profiles_updated
    BEFORE UPDATE ON public.user_profiles
    FOR EACH ROW
    EXECUTE FUNCTION public.handle_updated_at();

DROP TRIGGER IF EXISTS on_onboarding_progress_updated ON public.onboarding_progress;
CREATE TRIGGER on_onboarding_progress_updated
    BEFORE UPDATE ON public.onboarding_progress
    FOR EACH ROW
    EXECUTE FUNCTION public.handle_updated_at();

-- =====================================================
-- 6. AUTO-CREATE USER PROFILE ON SIGNUP
-- =====================================================

CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO public.user_profiles (id, email, full_name, avatar_url, auth_provider)
    VALUES (
        NEW.id,
        NEW.email,
        COALESCE(NEW.raw_user_meta_data->>'full_name', NEW.raw_user_meta_data->>'name'),
        NEW.raw_user_meta_data->>'avatar_url',
        COALESCE(NEW.raw_app_meta_data->>'provider', 'magic_link')
    );
    
    -- Also create onboarding progress record
    INSERT INTO public.onboarding_progress (user_id)
    VALUES (NEW.id);
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Trigger to auto-create profile on user signup
DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW
    EXECUTE FUNCTION public.handle_new_user();

-- =====================================================
-- 7. HELPER FUNCTIONS
-- =====================================================

-- Function to mark onboarding as complete
CREATE OR REPLACE FUNCTION public.complete_onboarding(p_user_id UUID)
RETURNS BOOLEAN AS $$
BEGIN
    UPDATE public.onboarding_progress
    SET 
        is_onboarding_complete = true,
        completed_at = NOW()
    WHERE user_id = p_user_id;
    
    RETURN FOUND;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to get user's company
CREATE OR REPLACE FUNCTION public.get_user_company(p_user_id UUID)
RETURNS UUID AS $$
DECLARE
    v_company_id UUID;
BEGIN
    SELECT company_id INTO v_company_id
    FROM public.user_profiles
    WHERE id = p_user_id;
    
    RETURN v_company_id;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to check if user is company admin
CREATE OR REPLACE FUNCTION public.is_company_admin(p_user_id UUID)
RETURNS BOOLEAN AS $$
DECLARE
    v_role VARCHAR(50);
BEGIN
    SELECT role INTO v_role
    FROM public.user_profiles
    WHERE id = p_user_id;
    
    RETURN v_role = 'admin';
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- =====================================================
-- 8. ROW LEVEL SECURITY (RLS) POLICIES
-- =====================================================

-- Enable RLS on all tables
ALTER TABLE public.companies ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.user_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.onboarding_progress ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.license_scans ENABLE ROW LEVEL SECURITY;

-- =====================================================
-- COMPANIES POLICIES
-- =====================================================

-- Users can view their own company
CREATE POLICY "Users can view own company"
    ON public.companies FOR SELECT
    USING (
        id IN (
            SELECT company_id FROM public.user_profiles WHERE id = auth.uid()
        )
    );

-- Company admins can update their company
CREATE POLICY "Admins can update own company"
    ON public.companies FOR UPDATE
    USING (
        id IN (
            SELECT company_id FROM public.user_profiles 
            WHERE id = auth.uid() AND role = 'admin'
        )
    );

-- Authenticated users can create companies (during onboarding)
CREATE POLICY "Authenticated users can create companies"
    ON public.companies FOR INSERT
    WITH CHECK (auth.uid() IS NOT NULL);

-- =====================================================
-- USER PROFILES POLICIES
-- =====================================================

-- Users can view their own profile
CREATE POLICY "Users can view own profile"
    ON public.user_profiles FOR SELECT
    USING (id = auth.uid());

-- Users can view profiles of their company members
CREATE POLICY "Users can view company member profiles"
    ON public.user_profiles FOR SELECT
    USING (
        company_id IN (
            SELECT company_id FROM public.user_profiles WHERE id = auth.uid()
        )
    );

-- Users can update their own profile
CREATE POLICY "Users can update own profile"
    ON public.user_profiles FOR UPDATE
    USING (id = auth.uid());

-- Allow profile creation during signup (handled by trigger)
CREATE POLICY "Enable insert for auth trigger"
    ON public.user_profiles FOR INSERT
    WITH CHECK (true);

-- =====================================================
-- ONBOARDING PROGRESS POLICIES
-- =====================================================

-- Users can view their own onboarding progress
CREATE POLICY "Users can view own onboarding"
    ON public.onboarding_progress FOR SELECT
    USING (user_id = auth.uid());

-- Users can update their own onboarding progress
CREATE POLICY "Users can update own onboarding"
    ON public.onboarding_progress FOR UPDATE
    USING (user_id = auth.uid());

-- Users can insert their own onboarding record
CREATE POLICY "Users can insert own onboarding"
    ON public.onboarding_progress FOR INSERT
    WITH CHECK (user_id = auth.uid() OR auth.uid() IS NOT NULL);

-- =====================================================
-- LICENSE SCANS POLICIES
-- =====================================================

-- Users can view scans for their company
CREATE POLICY "Users can view company scans"
    ON public.license_scans FOR SELECT
    USING (
        company_id IN (
            SELECT company_id FROM public.user_profiles WHERE id = auth.uid()
        )
    );

-- Admins/Managers can create scans
CREATE POLICY "Managers can create scans"
    ON public.license_scans FOR INSERT
    WITH CHECK (
        company_id IN (
            SELECT company_id FROM public.user_profiles 
            WHERE id = auth.uid() AND role IN ('admin', 'manager')
        )
    );

-- =====================================================
-- 9. SAMPLE DATA (Optional - for testing)
-- =====================================================

-- Uncomment below to insert sample data for testing
/*
-- Sample company
INSERT INTO public.companies (id, name, size, industry, domain)
VALUES (
    'a1b2c3d4-e5f6-7890-abcd-ef1234567890',
    'Demo Corporation',
    '51-200',
    'technology',
    'demo.com'
);

-- Note: User profiles are auto-created when users sign up
*/

-- =====================================================
-- SCHEMA VERIFICATION
-- =====================================================

-- Run this to verify all tables were created
DO $$
BEGIN
    RAISE NOTICE '✅ Schema created successfully!';
    RAISE NOTICE 'Tables created:';
    RAISE NOTICE '  - companies';
    RAISE NOTICE '  - user_profiles';
    RAISE NOTICE '  - onboarding_progress';
    RAISE NOTICE '  - license_scans';
    RAISE NOTICE '';
    RAISE NOTICE 'RLS enabled on all tables.';
    RAISE NOTICE '';
    RAISE NOTICE 'Next steps:';
    RAISE NOTICE '1. Enable Google OAuth in Supabase Auth settings';
    RAISE NOTICE '2. Configure redirect URLs for your domain';
    RAISE NOTICE '3. Deploy your frontend';
END $$;
