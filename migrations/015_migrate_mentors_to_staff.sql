-- Migration: Migrate mentors to staff table
-- Date: 2025-10-21
-- Description: Migrate all mentors to the staff table with appropriate role_title
--              and migrate mentor_conversations to staff_conversations

BEGIN;

-- Step 1: Migrate mentors to staff
INSERT INTO staff (
    id,
    handle,
    alias,
    name,
    description,
    persona,
    role_type,
    role_title,
    is_leadership_role,
    monitoring_scope,
    capabilities,
    allowed_tools,
    is_active,
    overall_rating,
    performance_metrics,
    created_at,
    updated_at
)
SELECT
    id,
    -- Generate handle from name (lowercase, replace spaces with underscores)
    LOWER(REPLACE(name, ' ', '_')) as handle,
    NULL as alias,  -- No alias for migrated mentors
    name,
    description,
    persona,
    'domain_expert' as role_type,  -- All mentors become domain experts
    CASE
        WHEN workspace = 'work' THEN 'Board Member'
        WHEN workspace = 'freelance' THEN 'Advisor'
        ELSE 'Mentor'
    END as role_title,
    FALSE as is_leadership_role,
    context_preferences as monitoring_scope,  -- Reuse context_preferences as monitoring_scope
    '[]'::jsonb as capabilities,
    '["list_projects", "get_project", "create_document"]'::jsonb as allowed_tools,
    is_active,
    NULL as overall_rating,
    '{
        "completed_tasks": 0,
        "avg_response_time_hours": 0.0,
        "quality_score": 0.0,
        "completion_rate": 0.0,
        "total_assignments": 0
    }'::jsonb as performance_metrics,
    created_at,
    updated_at
FROM mentors
WHERE id NOT IN (SELECT id FROM staff);  -- Avoid duplicates if migration is run twice

-- Step 2: Migrate mentor_conversations to staff_conversations
INSERT INTO staff_conversations (
    id,
    staff_id,
    message_type,
    content,
    is_group_discussion,
    group_discussion_id,
    created_at,
    updated_at
)
SELECT
    id,
    mentor_id as staff_id,
    message_type,
    content,
    FALSE as is_group_discussion,
    NULL as group_discussion_id,
    created_at,
    created_at as updated_at  -- mentor_conversations doesn't have updated_at
FROM mentor_conversations mc
WHERE mentor_id IN (SELECT id FROM mentors)
  AND id NOT IN (SELECT id FROM staff_conversations);  -- Avoid duplicates

COMMIT;

-- Note: This migration does NOT drop the mentors or mentor_conversations tables
-- They will be kept for reference/rollback purposes
-- To rollback:
-- DELETE FROM staff_conversations WHERE staff_id IN (SELECT id FROM mentors);
-- DELETE FROM staff WHERE id IN (SELECT id FROM mentors);
