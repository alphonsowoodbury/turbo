-- Migration: Add staff system (SQLite version)
-- Date: 2025-10-21
-- Description: Adds Staff system - AI domain experts with @ mention support

BEGIN;

-- ============================================================================
-- STAFF TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS staff (
    id TEXT PRIMARY KEY,
    handle VARCHAR(50) UNIQUE NOT NULL,
    alias VARCHAR(20) UNIQUE,
    name VARCHAR(200) NOT NULL,
    description TEXT NOT NULL,
    persona TEXT NOT NULL,
    role_type VARCHAR(50) NOT NULL,
    is_leadership_role INTEGER NOT NULL DEFAULT 0,
    monitoring_scope TEXT DEFAULT '{"entity_types": [], "tags": [], "focus": "", "metrics": []}',
    capabilities TEXT DEFAULT '[]',
    allowed_tools TEXT DEFAULT '["list_projects", "get_project", "create_document"]',
    is_active INTEGER NOT NULL DEFAULT 1,
    overall_rating REAL,
    performance_metrics TEXT DEFAULT '{"completed_tasks": 0, "avg_response_time_hours": 0.0, "quality_score": 0.0, "completion_rate": 0.0, "total_assignments": 0}',
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- ============================================================================
-- STAFF CONVERSATIONS TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS staff_conversations (
    id TEXT PRIMARY KEY,
    staff_id TEXT NOT NULL REFERENCES staff(id) ON DELETE CASCADE,
    message_type VARCHAR(20) NOT NULL CHECK (message_type IN ('user', 'assistant')),
    content TEXT NOT NULL,
    is_group_discussion INTEGER NOT NULL DEFAULT 0,
    group_discussion_id TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- ============================================================================
-- REVIEW REQUESTS TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS review_requests (
    id TEXT PRIMARY KEY,
    staff_id TEXT NOT NULL REFERENCES staff(id) ON DELETE CASCADE,
    entity_type VARCHAR(50) NOT NULL,
    entity_id TEXT NOT NULL,
    request_type VARCHAR(50) NOT NULL,
    description TEXT NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'reviewed', 'dismissed')),
    reviewed_at TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- ============================================================================
-- INDEXES FOR PERFORMANCE
-- ============================================================================
CREATE INDEX IF NOT EXISTS idx_staff_handle ON staff(handle);
CREATE INDEX IF NOT EXISTS idx_staff_role_type ON staff(role_type);
CREATE INDEX IF NOT EXISTS idx_staff_is_leadership ON staff(is_leadership_role);
CREATE INDEX IF NOT EXISTS idx_staff_is_active ON staff(is_active);
CREATE INDEX IF NOT EXISTS idx_staff_alias ON staff(alias);

CREATE INDEX IF NOT EXISTS idx_staff_conversations_staff_id ON staff_conversations(staff_id);
CREATE INDEX IF NOT EXISTS idx_staff_conversations_created_at ON staff_conversations(created_at);
CREATE INDEX IF NOT EXISTS idx_staff_conversations_group ON staff_conversations(group_discussion_id);

CREATE INDEX IF NOT EXISTS idx_review_requests_staff_id ON review_requests(staff_id);
CREATE INDEX IF NOT EXISTS idx_review_requests_entity ON review_requests(entity_type, entity_id);
CREATE INDEX IF NOT EXISTS idx_review_requests_status ON review_requests(status);

COMMIT;
