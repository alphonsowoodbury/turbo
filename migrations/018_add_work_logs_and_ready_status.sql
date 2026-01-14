-- Migration: Add work logs table and ready status
-- Date: 2025-10-22

-- Create work logs table for tracking issue work sessions
CREATE TABLE IF NOT EXISTS issue_work_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    issue_id UUID NOT NULL REFERENCES issues(id) ON DELETE CASCADE,

    -- Timestamps
    started_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    ended_at TIMESTAMP,

    -- Who performed the work
    started_by VARCHAR(50) NOT NULL,  -- 'user', 'ai:context', 'ai:turbo'

    -- Git commit reference
    commit_url VARCHAR(500),

    -- Standard timestamps
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for efficient queries
CREATE INDEX IF NOT EXISTS idx_work_logs_issue_id ON issue_work_logs(issue_id);
CREATE INDEX IF NOT EXISTS idx_work_logs_started_at ON issue_work_logs(started_at);
CREATE INDEX IF NOT EXISTS idx_work_logs_ended_at ON issue_work_logs(ended_at);
CREATE INDEX IF NOT EXISTS idx_work_logs_started_by ON issue_work_logs(started_by);

-- Note: The 'ready' status will be added to the status enum.
-- PostgreSQL doesn't have a simple ALTER TYPE command for enums in all versions,
-- so we'll handle status validation at the application level.
-- The valid statuses are now: open, ready, in_progress, review, testing, closed
