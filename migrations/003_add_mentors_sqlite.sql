-- Migration: Add mentors and mentor_conversations tables (SQLite version)
-- Date: 2025-10-21
-- Description: Adds mentor feature with workspace-aware AI assistants

BEGIN;

-- Create mentors table
CREATE TABLE IF NOT EXISTS mentors (
    id TEXT PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    description TEXT NOT NULL,
    persona TEXT NOT NULL,
    workspace VARCHAR(20) NOT NULL DEFAULT 'personal',
    work_company VARCHAR(100),
    context_preferences TEXT DEFAULT '{"include_projects": true, "include_issues": true, "include_documents": true, "include_influencers": true, "max_items": 10}',
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Create mentor_conversations table
CREATE TABLE IF NOT EXISTS mentor_conversations (
    id TEXT PRIMARY KEY,
    mentor_id TEXT NOT NULL REFERENCES mentors(id) ON DELETE CASCADE,
    message_type VARCHAR(20) NOT NULL CHECK (message_type IN ('user', 'assistant')),
    content TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_mentors_workspace ON mentors(workspace);
CREATE INDEX IF NOT EXISTS idx_mentors_is_active ON mentors(is_active);
CREATE INDEX IF NOT EXISTS idx_mentor_conversations_mentor_id ON mentor_conversations(mentor_id);
CREATE INDEX IF NOT EXISTS idx_mentor_conversations_created_at ON mentor_conversations(created_at);

COMMIT;
