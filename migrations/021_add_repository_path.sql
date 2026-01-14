-- Migration: Add repository_path to projects table
-- This allows each project to specify its local git repository path
-- for autonomous worktree creation

-- Add repository_path column
ALTER TABLE projects ADD COLUMN IF NOT EXISTS repository_path VARCHAR(500);

-- Add index for faster lookups
CREATE INDEX IF NOT EXISTS idx_projects_repository_path ON projects(repository_path) WHERE repository_path IS NOT NULL;

-- Add comment
COMMENT ON COLUMN projects.repository_path IS 'Local filesystem path to the git repository for this project (e.g., /Users/username/Documents/Code/PycharmProjects/context)';
