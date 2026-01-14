-- Migration: Migrate mentors to staff table (SQLite version)
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
    lower(replace(name, ' ', '_')) as handle,
    NULL as alias,
    name,
    description,
    persona,
    'domain_expert' as role_type,
    CASE
        WHEN workspace = 'work' THEN 'Board Member'
        WHEN workspace = 'freelance' THEN 'Advisor'
        ELSE 'Mentor'
    END as role_title,
    0 as is_leadership_role,
    context_preferences as monitoring_scope,
    '[]' as capabilities,
    '["list_projects", "get_project", "create_document"]' as allowed_tools,
    is_active,
    NULL as overall_rating,
    '{"completed_tasks": 0, "avg_response_time_hours": 0.0, "quality_score": 0.0, "completion_rate": 0.0, "total_assignments": 0}' as performance_metrics,
    created_at,
    updated_at
FROM mentors
WHERE id NOT IN (SELECT id FROM staff);

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
    0 as is_group_discussion,
    NULL as group_discussion_id,
    created_at,
    created_at as updated_at
FROM mentor_conversations mc
WHERE mentor_id IN (SELECT id FROM mentors)
  AND id NOT IN (SELECT id FROM staff_conversations);

COMMIT;
