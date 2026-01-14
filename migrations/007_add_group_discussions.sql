-- Migration: Add group discussions table for All Hands and staff group chats
-- Date: 2025-10-20
-- Description: Adds group_discussions table for multi-staff conversations

BEGIN;

-- ============================================================================
-- GROUP DISCUSSIONS TABLE
-- ============================================================================
-- Group discussion rooms for staff members (All Hands, department meetings, etc.)
CREATE TABLE IF NOT EXISTS group_discussions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(200) NOT NULL,
    description TEXT,
    discussion_type VARCHAR(50) NOT NULL DEFAULT 'all_hands',
    participant_ids JSONB NOT NULL DEFAULT '[]'::jsonb,
    status VARCHAR(20) NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'archived')),
    message_count INTEGER NOT NULL DEFAULT 0,
    last_activity_at TIMESTAMP WITH TIME ZONE,
    settings JSONB DEFAULT '{"auto_summarize": true, "allow_user_participation": true, "max_messages": null}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- ============================================================================
-- INDEXES FOR PERFORMANCE
-- ============================================================================

CREATE INDEX IF NOT EXISTS idx_group_discussions_type ON group_discussions(discussion_type);
CREATE INDEX IF NOT EXISTS idx_group_discussions_status ON group_discussions(status);
CREATE INDEX IF NOT EXISTS idx_group_discussions_last_activity ON group_discussions(last_activity_at DESC NULLS LAST);
CREATE INDEX IF NOT EXISTS idx_group_discussions_active ON group_discussions(status, last_activity_at DESC) WHERE status = 'active';

-- ============================================================================
-- TABLE AND COLUMN COMMENTS FOR DOCUMENTATION
-- ============================================================================

COMMENT ON TABLE group_discussions IS 'Group discussion rooms for multi-staff conversations (All Hands, department meetings, etc.)';
COMMENT ON COLUMN group_discussions.name IS 'Display name of the discussion room';
COMMENT ON COLUMN group_discussions.description IS 'Optional description of the discussion purpose';
COMMENT ON COLUMN group_discussions.discussion_type IS 'Type: all_hands, department, ad_hoc, etc.';
COMMENT ON COLUMN group_discussions.participant_ids IS 'JSON array of staff UUIDs participating in the discussion';
COMMENT ON COLUMN group_discussions.status IS 'Discussion status: active or archived';
COMMENT ON COLUMN group_discussions.message_count IS 'Total number of messages in the discussion';
COMMENT ON COLUMN group_discussions.last_activity_at IS 'Timestamp of last message in the discussion';
COMMENT ON COLUMN group_discussions.settings IS 'JSON settings: auto_summarize, allow_user_participation, max_messages, etc.';

-- ============================================================================
-- CREATE DEFAULT "ALL HANDS" DISCUSSION ROOM
-- ============================================================================

-- Get all active staff member IDs
WITH active_staff AS (
    SELECT jsonb_agg(id) AS staff_ids
    FROM staff
    WHERE is_active = true
)
INSERT INTO group_discussions (name, description, discussion_type, participant_ids, status)
SELECT
    'All Hands',
    'Company-wide discussion room for all AI staff members to collaborate and discuss initiatives.',
    'all_hands',
    COALESCE(staff_ids, '[]'::jsonb),
    'active'
FROM active_staff
ON CONFLICT DO NOTHING;

COMMIT;
