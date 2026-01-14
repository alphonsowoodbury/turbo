-- Migration: Convert Career Coach from mentor to staff member
-- This migration moves the Career Coach from the mentors table to the staff table

-- First, create the Career Coach as a staff member
INSERT INTO staff (
    id,
    name,
    handle,
    role_type,
    persona,
    capabilities,
    workspace,
    is_active,
    created_at,
    updated_at
)
SELECT
    id,
    name,
    'CareerCoach' as handle,
    'domain_expert' as role_type,
    persona,
    ARRAY['career_guidance', 'resume_review', 'interview_prep', 'salary_negotiation', 'job_search_strategy'] as capabilities,
    workspace,
    is_active,
    created_at,
    updated_at
FROM mentors
WHERE name = 'Career Coach'
ON CONFLICT (id) DO NOTHING;

-- Migrate mentor conversation messages to staff conversations
INSERT INTO staff_conversations (
    id,
    staff_id,
    message_type,
    content,
    created_at
)
SELECT
    mc.id,
    mc.mentor_id as staff_id,
    CASE
        WHEN mc.role = 'user' THEN 'user'
        ELSE 'assistant'
    END as message_type,
    mc.content,
    mc.created_at
FROM mentor_conversations mc
WHERE mc.mentor_id = (SELECT id FROM mentors WHERE name = 'Career Coach')
ON CONFLICT (id) DO NOTHING;

-- Note: We're keeping the mentor data for now as a backup
-- Once confirmed working, we can drop the mentor tables in a future migration

-- Add comment
COMMENT ON TABLE staff IS 'Staff members including domain experts like Career Coach. Mentors have been migrated to this table.';
