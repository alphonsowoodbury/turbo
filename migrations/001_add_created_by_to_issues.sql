-- Migration: Add created_by field to issues table
-- Created: 2025-10-13
-- Description: Track who created each issue (user email or AI model name)

-- Add created_by column
ALTER TABLE issues ADD COLUMN IF NOT EXISTS created_by VARCHAR(255);

-- Create index for faster queries on created_by
CREATE INDEX IF NOT EXISTS idx_issues_created_by ON issues(created_by);

-- Add comment to column
COMMENT ON COLUMN issues.created_by IS 'User email or AI model name (format: "AI: model_name")';
