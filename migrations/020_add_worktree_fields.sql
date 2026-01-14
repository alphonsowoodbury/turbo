-- Migration 020: Add Git Worktree Fields to Work Logs
-- Description: Add worktree_path and branch_name columns to track git worktrees during work sessions
-- Date: 2025-10-23

-- ==========================================
-- 1. ADD WORKTREE COLUMNS TO WORK LOGS
-- ==========================================

-- Add worktree_path column (path to git worktree directory)
ALTER TABLE issue_work_logs
ADD COLUMN IF NOT EXISTS worktree_path VARCHAR(500) NULL;

-- Add branch_name column (git branch name for the worktree)
ALTER TABLE issue_work_logs
ADD COLUMN IF NOT EXISTS branch_name VARCHAR(100) NULL;

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_work_logs_worktree_path ON issue_work_logs(worktree_path);
CREATE INDEX IF NOT EXISTS idx_work_logs_branch_name ON issue_work_logs(branch_name);

-- Add comments
COMMENT ON COLUMN issue_work_logs.worktree_path IS 'Path to git worktree (e.g., ~/worktrees/Project-CNTXT-1)';
COMMENT ON COLUMN issue_work_logs.branch_name IS 'Git branch name (e.g., CNTXT-1/fix-auth-bug)';
