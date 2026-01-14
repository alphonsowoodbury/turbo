-- Migration: Add application_url field to job_postings table
-- Description: Stores the direct application URL (company's application page)
--              separate from source_url (aggregator listing page)
-- Date: 2025-10-25

-- Add application_url column
ALTER TABLE job_postings
ADD COLUMN IF NOT EXISTS application_url TEXT;

-- Add comment explaining the field
COMMENT ON COLUMN job_postings.application_url IS
'Direct URL to apply for the job on the company''s application page. Different from source_url which points to the job board listing.';

-- Create index for faster lookups when filtering by application URL availability
CREATE INDEX IF NOT EXISTS idx_job_postings_has_application_url
ON job_postings ((application_url IS NOT NULL));
