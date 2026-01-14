-- Migration: Add notes table and note_tags association table
-- Description: Creates notes table for quick capture and note_tags for many-to-many relationship with tags

-- Create notes table
CREATE TABLE IF NOT EXISTS notes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(500) NOT NULL,
    content TEXT,
    workspace VARCHAR(50) NOT NULL DEFAULT 'personal',
    work_company VARCHAR(100),
    is_archived BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for notes
CREATE INDEX IF NOT EXISTS idx_notes_title ON notes(title);
CREATE INDEX IF NOT EXISTS idx_notes_workspace ON notes(workspace);
CREATE INDEX IF NOT EXISTS idx_notes_work_company ON notes(work_company);
CREATE INDEX IF NOT EXISTS idx_notes_is_archived ON notes(is_archived);
CREATE INDEX IF NOT EXISTS idx_notes_created_at ON notes(created_at);

-- Create note_tags association table
CREATE TABLE IF NOT EXISTS note_tags (
    note_id UUID NOT NULL REFERENCES notes(id) ON DELETE CASCADE,
    tag_id UUID NOT NULL REFERENCES tags(id) ON DELETE CASCADE,
    PRIMARY KEY (note_id, tag_id)
);

-- Update Comment entity_type enum to include 'note'
-- Note: This assumes entity_type is a VARCHAR, not an ENUM type
-- If it's an ENUM, you'll need to use ALTER TYPE instead
