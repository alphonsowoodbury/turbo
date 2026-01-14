-- Migration: Add Job Search and Job Postings tables
-- Description: Enables automated job search, discovery, and tracking of job postings
-- Date: 2025-10-25

-- ============================================================================
-- Job Postings Table
-- ============================================================================
-- Stores discovered job postings from various sources before they become applications
CREATE TABLE IF NOT EXISTS job_postings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Source Information
    source VARCHAR(100) NOT NULL,  -- 'indeed', 'linkedin', 'builtin', 'hackernews', 'company_site'
    source_url TEXT NOT NULL,  -- Original job posting URL
    external_id VARCHAR(255),  -- Job ID from the source platform

    -- Company Information
    company_id UUID REFERENCES companies(id) ON DELETE SET NULL,  -- Link to existing company or NULL
    company_name VARCHAR(255) NOT NULL,  -- Raw company name from posting

    -- Job Details
    job_title VARCHAR(500) NOT NULL,
    job_description TEXT,

    -- Location & Remote
    location VARCHAR(255),
    remote_policy VARCHAR(50),  -- 'remote', 'hybrid', 'onsite', 'unknown'

    -- Compensation
    salary_min INTEGER,
    salary_max INTEGER,
    salary_currency VARCHAR(10) DEFAULT 'USD',

    -- Requirements & Skills
    required_skills TEXT[],  -- Array of required skills mentioned
    preferred_skills TEXT[],  -- Array of preferred skills
    required_keywords TEXT[],  -- Keywords found that matched search criteria

    -- Metadata
    posted_date TIMESTAMP,  -- When job was posted on the source platform
    discovered_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,  -- When we found it
    expires_date TIMESTAMP,  -- Job posting expiration if available

    -- Status & Scoring
    status VARCHAR(50) DEFAULT 'new',  -- 'new', 'interested', 'not_interested', 'applied', 'expired'
    match_score FLOAT,  -- 0-100 score of how well it matches criteria
    match_reasons JSONB,  -- Details about why it matched

    -- Raw Data
    raw_data JSONB,  -- Full scraped data for reference

    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Constraints
    UNIQUE(source, external_id)  -- Prevent duplicates from same source
);

-- Indexes for job postings
CREATE INDEX IF NOT EXISTS idx_job_postings_status ON job_postings(status);
CREATE INDEX IF NOT EXISTS idx_job_postings_source ON job_postings(source);
CREATE INDEX IF NOT EXISTS idx_job_postings_match_score ON job_postings(match_score DESC);
CREATE INDEX IF NOT EXISTS idx_job_postings_posted_date ON job_postings(posted_date DESC);
CREATE INDEX IF NOT EXISTS idx_job_postings_company_id ON job_postings(company_id);
CREATE INDEX IF NOT EXISTS idx_job_postings_discovered_date ON job_postings(discovered_date DESC);


-- ============================================================================
-- Search Criteria Table
-- ============================================================================
-- Stores job search preferences and criteria
CREATE TABLE IF NOT EXISTS search_criteria (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Criteria Name
    name VARCHAR(255) NOT NULL,  -- e.g., "Senior Data Engineer Remote"
    description TEXT,
    is_active BOOLEAN DEFAULT true,

    -- Job Titles
    job_titles TEXT[],  -- Array of target job titles

    -- Location Preferences
    locations TEXT[],  -- Preferred locations
    excluded_states TEXT[],  -- States to exclude

    -- Remote Policy
    remote_policies TEXT[],  -- 'remote', 'hybrid', 'onsite'
    exclude_onsite BOOLEAN DEFAULT false,

    -- Salary Requirements
    salary_minimum INTEGER,
    salary_target INTEGER,

    -- Keywords
    required_keywords TEXT[],  -- Must have these keywords
    preferred_keywords TEXT[],  -- Nice to have
    excluded_keywords TEXT[],  -- Exclude jobs with these

    -- Company Filters
    company_sizes TEXT[],  -- 'startup', 'small', 'medium', 'large', 'enterprise'
    industries TEXT[],  -- Preferred industries
    excluded_industries TEXT[],  -- Industries to avoid

    -- Job Boards
    enabled_sources TEXT[],  -- Which job boards to search

    -- Automation Settings
    auto_search_enabled BOOLEAN DEFAULT false,
    search_frequency_hours INTEGER DEFAULT 24,  -- How often to search
    last_search_at TIMESTAMP,
    next_search_at TIMESTAMP,

    -- Scoring Weights
    scoring_weights JSONB DEFAULT '{"salary": 0.3, "location": 0.2, "keywords": 0.3, "title": 0.2}'::JSONB,

    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for search criteria
CREATE INDEX IF NOT EXISTS idx_search_criteria_active ON search_criteria(is_active);
CREATE INDEX IF NOT EXISTS idx_search_criteria_next_search ON search_criteria(next_search_at);


-- ============================================================================
-- Job Search History Table
-- ============================================================================
-- Tracks each search execution
CREATE TABLE IF NOT EXISTS job_search_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    search_criteria_id UUID REFERENCES search_criteria(id) ON DELETE CASCADE,

    -- Search Details
    source VARCHAR(100) NOT NULL,  -- Which job board was searched
    query_params JSONB,  -- Parameters used for the search

    -- Results
    jobs_found INTEGER DEFAULT 0,
    jobs_matched INTEGER DEFAULT 0,  -- How many met criteria
    jobs_new INTEGER DEFAULT 0,  -- How many were new (not seen before)

    -- Status
    status VARCHAR(50) DEFAULT 'running',  -- 'running', 'completed', 'failed'
    error_message TEXT,

    -- Timing
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    duration_seconds INTEGER,

    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for search history
CREATE INDEX IF NOT EXISTS idx_job_search_history_criteria ON job_search_history(search_criteria_id);
CREATE INDEX IF NOT EXISTS idx_job_search_history_created ON job_search_history(created_at DESC);


-- ============================================================================
-- Link Job Postings to Search Criteria (Many-to-Many)
-- ============================================================================
CREATE TABLE IF NOT EXISTS job_posting_matches (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    job_posting_id UUID REFERENCES job_postings(id) ON DELETE CASCADE,
    search_criteria_id UUID REFERENCES search_criteria(id) ON DELETE CASCADE,

    match_score FLOAT,  -- Score for this specific criteria
    match_reasons JSONB,  -- Why it matched this criteria

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(job_posting_id, search_criteria_id)
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_job_posting_matches_posting ON job_posting_matches(job_posting_id);
CREATE INDEX IF NOT EXISTS idx_job_posting_matches_criteria ON job_posting_matches(search_criteria_id);


-- ============================================================================
-- Triggers for updated_at timestamps
-- ============================================================================
CREATE OR REPLACE FUNCTION update_job_search_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_job_postings_updated_at
    BEFORE UPDATE ON job_postings
    FOR EACH ROW
    EXECUTE FUNCTION update_job_search_updated_at();

CREATE TRIGGER update_search_criteria_updated_at
    BEFORE UPDATE ON search_criteria
    FOR EACH ROW
    EXECUTE FUNCTION update_job_search_updated_at();
