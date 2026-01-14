-- Migration: Add interest fields to job_postings
-- Description: Add interest_level and interest_notes to track user interest in job postings
-- Date: 2025-10-25

ALTER TABLE job_postings
ADD COLUMN IF NOT EXISTS interest_level INTEGER CHECK (interest_level >= 1 AND interest_level <= 5),
ADD COLUMN IF NOT EXISTS interest_notes TEXT;

-- Index for filtering by interest level
CREATE INDEX IF NOT EXISTS idx_job_postings_interest ON job_postings(interest_level) WHERE interest_level IS NOT NULL;
