-- Migration: Add assigned_to fields to projects, documents, and blueprints
-- Description: Add polymorphic assignment (owner) tracking to all entities
-- Date: 2025-10-20

-- Add assigned_to fields to projects table
ALTER TABLE projects
ADD COLUMN IF NOT EXISTS assigned_to_type VARCHAR(20),
ADD COLUMN IF NOT EXISTS assigned_to_id UUID;

-- Add indexes for projects
CREATE INDEX IF NOT EXISTS idx_projects_assigned_to_type ON projects(assigned_to_type);
CREATE INDEX IF NOT EXISTS idx_projects_assigned_to_id ON projects(assigned_to_id);

-- Add assigned_to fields to documents table
ALTER TABLE documents
ADD COLUMN IF NOT EXISTS assigned_to_type VARCHAR(20),
ADD COLUMN IF NOT EXISTS assigned_to_id UUID;

-- Add indexes for documents
CREATE INDEX IF NOT EXISTS idx_documents_assigned_to_type ON documents(assigned_to_type);
CREATE INDEX IF NOT EXISTS idx_documents_assigned_to_id ON documents(assigned_to_id);

-- Add assigned_to fields to blueprints table
ALTER TABLE blueprints
ADD COLUMN IF NOT EXISTS assigned_to_type VARCHAR(20),
ADD COLUMN IF NOT EXISTS assigned_to_id UUID;

-- Add indexes for blueprints
CREATE INDEX IF NOT EXISTS idx_blueprints_assigned_to_type ON blueprints(assigned_to_type);
CREATE INDEX IF NOT EXISTS idx_blueprints_assigned_to_id ON blueprints(assigned_to_id);

-- Comments explaining the fields
COMMENT ON COLUMN projects.assigned_to_type IS 'Polymorphic owner type: user or staff';
COMMENT ON COLUMN projects.assigned_to_id IS 'UUID of the assigned user or staff member';

COMMENT ON COLUMN documents.assigned_to_type IS 'Polymorphic owner type: user or staff';
COMMENT ON COLUMN documents.assigned_to_id IS 'UUID of the assigned user or staff member';

COMMENT ON COLUMN blueprints.assigned_to_type IS 'Polymorphic owner type: user or staff';
COMMENT ON COLUMN blueprints.assigned_to_id IS 'UUID of the assigned user or staff member';
