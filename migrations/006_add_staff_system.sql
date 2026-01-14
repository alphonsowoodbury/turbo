-- Migration: Add staff system with assignments, conversations, and review requests
-- Date: 2025-10-19
-- Description: Adds Staff system - AI domain experts with @ mention support, polymorphic assignments, and review requests

BEGIN;

-- ============================================================================
-- STAFF TABLE
-- ============================================================================
-- Core staff table for AI domain experts and leadership roles
CREATE TABLE IF NOT EXISTS staff (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    handle VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(200) NOT NULL,
    description TEXT NOT NULL,
    persona TEXT NOT NULL,
    role_type VARCHAR(50) NOT NULL,
    is_leadership_role BOOLEAN NOT NULL DEFAULT false,
    monitoring_scope JSONB DEFAULT '{"entity_types": [], "tags": [], "focus": "", "metrics": []}'::jsonb,
    capabilities JSONB DEFAULT '[]'::jsonb,
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- ============================================================================
-- STAFF CONVERSATIONS TABLE
-- ============================================================================
-- Conversation history with staff members (1-on-1 and group discussions)
CREATE TABLE IF NOT EXISTS staff_conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    staff_id UUID NOT NULL REFERENCES staff(id) ON DELETE CASCADE,
    message_type VARCHAR(20) NOT NULL CHECK (message_type IN ('user', 'assistant')),
    content TEXT NOT NULL,
    is_group_discussion BOOLEAN NOT NULL DEFAULT false,
    group_discussion_id UUID,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- ============================================================================
-- REVIEW REQUESTS TABLE
-- ============================================================================
-- Review requests from staff to user (scope validation, feedback, approvals)
CREATE TABLE IF NOT EXISTS review_requests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    staff_id UUID NOT NULL REFERENCES staff(id) ON DELETE CASCADE,
    entity_type VARCHAR(50) NOT NULL,
    entity_id UUID NOT NULL,
    request_type VARCHAR(50) NOT NULL,
    description TEXT NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'reviewed', 'dismissed')),
    reviewed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- ============================================================================
-- ADD ASSIGNMENT FIELDS TO EXISTING TABLES
-- ============================================================================

-- Add assignment fields to issues table
ALTER TABLE issues
ADD COLUMN IF NOT EXISTS assigned_to_type VARCHAR(20),
ADD COLUMN IF NOT EXISTS assigned_to_id UUID;

-- Add assignment fields to initiatives table
ALTER TABLE initiatives
ADD COLUMN IF NOT EXISTS assigned_to_type VARCHAR(20),
ADD COLUMN IF NOT EXISTS assigned_to_id UUID;

-- Add assignment fields to milestones table
ALTER TABLE milestones
ADD COLUMN IF NOT EXISTS assigned_to_type VARCHAR(20),
ADD COLUMN IF NOT EXISTS assigned_to_id UUID;

-- ============================================================================
-- INDEXES FOR PERFORMANCE
-- ============================================================================

-- Staff indexes
CREATE INDEX IF NOT EXISTS idx_staff_handle ON staff(handle);
CREATE INDEX IF NOT EXISTS idx_staff_role_type ON staff(role_type);
CREATE INDEX IF NOT EXISTS idx_staff_is_leadership ON staff(is_leadership_role);
CREATE INDEX IF NOT EXISTS idx_staff_is_active ON staff(is_active);
CREATE INDEX IF NOT EXISTS idx_staff_active_leadership ON staff(is_active, is_leadership_role);

-- Staff conversations indexes
CREATE INDEX IF NOT EXISTS idx_staff_conversations_staff_id ON staff_conversations(staff_id);
CREATE INDEX IF NOT EXISTS idx_staff_conversations_created_at ON staff_conversations(created_at);
CREATE INDEX IF NOT EXISTS idx_staff_conversations_staff_created ON staff_conversations(staff_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_staff_conversations_group ON staff_conversations(group_discussion_id) WHERE group_discussion_id IS NOT NULL;

-- Review requests indexes
CREATE INDEX IF NOT EXISTS idx_review_requests_staff_id ON review_requests(staff_id);
CREATE INDEX IF NOT EXISTS idx_review_requests_entity ON review_requests(entity_type, entity_id);
CREATE INDEX IF NOT EXISTS idx_review_requests_status ON review_requests(status);
CREATE INDEX IF NOT EXISTS idx_review_requests_type ON review_requests(request_type);
CREATE INDEX IF NOT EXISTS idx_review_requests_pending ON review_requests(status, created_at DESC) WHERE status = 'pending';

-- Assignment indexes on issues
CREATE INDEX IF NOT EXISTS idx_issues_assigned_to_type ON issues(assigned_to_type) WHERE assigned_to_type IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_issues_assigned_to_id ON issues(assigned_to_id) WHERE assigned_to_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_issues_assignment ON issues(assigned_to_type, assigned_to_id) WHERE assigned_to_type IS NOT NULL;

-- Assignment indexes on initiatives
CREATE INDEX IF NOT EXISTS idx_initiatives_assigned_to_type ON initiatives(assigned_to_type) WHERE assigned_to_type IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_initiatives_assigned_to_id ON initiatives(assigned_to_id) WHERE assigned_to_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_initiatives_assignment ON initiatives(assigned_to_type, assigned_to_id) WHERE assigned_to_type IS NOT NULL;

-- Assignment indexes on milestones
CREATE INDEX IF NOT EXISTS idx_milestones_assigned_to_type ON milestones(assigned_to_type) WHERE assigned_to_type IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_milestones_assigned_to_id ON milestones(assigned_to_id) WHERE assigned_to_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_milestones_assignment ON milestones(assigned_to_type, assigned_to_id) WHERE assigned_to_type IS NOT NULL;

-- ============================================================================
-- TABLE AND COLUMN COMMENTS FOR DOCUMENTATION
-- ============================================================================

-- Staff table comments
COMMENT ON TABLE staff IS 'AI domain experts and leadership roles that can be @ mentioned and assigned work';
COMMENT ON COLUMN staff.handle IS 'Unique handle for @ mentions (e.g., ChiefOfStaff, SecurityLead)';
COMMENT ON COLUMN staff.name IS 'Display name of the staff member';
COMMENT ON COLUMN staff.persona IS 'Detailed AI persona used for Claude API responses';
COMMENT ON COLUMN staff.role_type IS 'Role type: leadership or domain_expert';
COMMENT ON COLUMN staff.is_leadership_role IS 'Leadership roles have universal edit permissions';
COMMENT ON COLUMN staff.monitoring_scope IS 'JSON defining what entities/tags/metrics this staff monitors';
COMMENT ON COLUMN staff.capabilities IS 'JSON array of capabilities (analysis, refinement, content_creation, etc.)';

-- Staff conversations comments
COMMENT ON TABLE staff_conversations IS 'Conversation history with staff members (1-on-1 and group discussions)';
COMMENT ON COLUMN staff_conversations.message_type IS 'Message type: user or assistant';
COMMENT ON COLUMN staff_conversations.is_group_discussion IS 'True if this message is part of a group discussion';
COMMENT ON COLUMN staff_conversations.group_discussion_id IS 'UUID linking messages in the same group discussion';

-- Review requests comments
COMMENT ON TABLE review_requests IS 'Review requests from staff to user for feedback, scope validation, approvals';
COMMENT ON COLUMN review_requests.entity_type IS 'Type of entity being reviewed: issue, initiative, milestone, project';
COMMENT ON COLUMN review_requests.request_type IS 'Type of review: scope_validation, feedback, approval, architecture_review, security_review';
COMMENT ON COLUMN review_requests.status IS 'Status: pending, reviewed, or dismissed';

-- Assignment fields comments
COMMENT ON COLUMN issues.assigned_to_type IS 'Polymorphic assignment type: user or staff';
COMMENT ON COLUMN issues.assigned_to_id IS 'UUID of assigned user or staff member';
COMMENT ON COLUMN initiatives.assigned_to_type IS 'Polymorphic assignment type: user or staff';
COMMENT ON COLUMN initiatives.assigned_to_id IS 'UUID of assigned user or staff member';
COMMENT ON COLUMN milestones.assigned_to_type IS 'Polymorphic assignment type: user or staff';
COMMENT ON COLUMN milestones.assigned_to_id IS 'UUID of assigned user or staff member';

COMMIT;
