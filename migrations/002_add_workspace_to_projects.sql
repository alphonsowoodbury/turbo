-- Migration: Add workspace and work_company fields to projects table
-- Date: 2025-10-16
-- Description: Adds workspace context filtering to allow switching between personal, freelance, and work projects

-- Add workspace column with default 'personal'
ALTER TABLE projects
ADD COLUMN workspace VARCHAR(20) NOT NULL DEFAULT 'personal';

-- Add work_company column for company-specific work contexts
ALTER TABLE projects
ADD COLUMN work_company VARCHAR(100);

-- Create index on workspace for fast filtering
CREATE INDEX idx_projects_workspace ON projects(workspace);

-- Add comment for documentation
COMMENT ON COLUMN projects.workspace IS 'Workspace context: personal, freelance, or work';
COMMENT ON COLUMN projects.work_company IS 'Company name for work workspace (e.g., JPMC, Google)';
