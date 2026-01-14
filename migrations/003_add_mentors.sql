-- Migration: Add mentors and mentor_conversations tables
-- Date: 2025-10-16
-- Description: Adds mentor feature with workspace-aware AI assistants powered by Claude Code

BEGIN;

-- Create mentors table
CREATE TABLE IF NOT EXISTS mentors (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(200) NOT NULL,
    description TEXT NOT NULL,
    persona TEXT NOT NULL,
    workspace VARCHAR(20) NOT NULL DEFAULT 'personal',
    work_company VARCHAR(100),
    context_preferences JSONB DEFAULT '{"include_projects": true, "include_issues": true, "include_documents": true, "include_influencers": true, "max_items": 10}'::jsonb,
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Create mentor_conversations table
CREATE TABLE IF NOT EXISTS mentor_conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    mentor_id UUID NOT NULL REFERENCES mentors(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL CHECK (role IN ('user', 'assistant')),
    content TEXT NOT NULL,
    context_snapshot JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_mentors_workspace ON mentors(workspace);
CREATE INDEX IF NOT EXISTS idx_mentors_is_active ON mentors(is_active);
CREATE INDEX IF NOT EXISTS idx_mentors_workspace_active ON mentors(workspace, is_active);
CREATE INDEX IF NOT EXISTS idx_mentor_conversations_mentor_id ON mentor_conversations(mentor_id);
CREATE INDEX IF NOT EXISTS idx_mentor_conversations_created_at ON mentor_conversations(created_at);
CREATE INDEX IF NOT EXISTS idx_mentor_conversations_mentor_created ON mentor_conversations(mentor_id, created_at DESC);

-- Add comments for documentation
COMMENT ON TABLE mentors IS 'AI mentor assistants powered by Claude Code with workspace-specific context';
COMMENT ON TABLE mentor_conversations IS 'Persistent conversation history for mentors';
COMMENT ON COLUMN mentors.workspace IS 'Workspace context: personal, freelance, or work';
COMMENT ON COLUMN mentors.work_company IS 'Company name for work workspace (e.g., JPMC)';
COMMENT ON COLUMN mentors.persona IS 'System prompt defining mentor personality and expertise';
COMMENT ON COLUMN mentors.context_preferences IS 'JSON configuration for what context to include in conversations';
COMMENT ON COLUMN mentor_conversations.role IS 'Message role: user or assistant';
COMMENT ON COLUMN mentor_conversations.context_snapshot IS 'Snapshot of workspace context used for this message';

COMMIT;
