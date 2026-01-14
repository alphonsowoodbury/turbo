-- Migration: Add allowed_tools to staff table
-- Description: Add configurable tool access control for staff members
-- Date: 2025-10-20

-- Add allowed_tools JSONB field with default tools
ALTER TABLE staff
ADD COLUMN IF NOT EXISTS allowed_tools JSONB NOT NULL DEFAULT '["list_projects", "get_project", "create_document"]'::jsonb;

-- Comment explaining the field
COMMENT ON COLUMN staff.allowed_tools IS 'List of tool names this staff member can access for function calling';

-- Update existing staff members to have the default tools
UPDATE staff SET allowed_tools = '["list_projects", "get_project", "create_document"]'::jsonb WHERE allowed_tools IS NULL;
