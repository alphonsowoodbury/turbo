-- Migration: Add polymorphic comments support
-- This migration converts comments from issue-only to support all entity types
-- (issues, projects, milestones, initiatives, documents, literature, blueprints)

BEGIN;

-- Step 1: Add new columns (nullable initially for migration)
ALTER TABLE comments ADD COLUMN IF NOT EXISTS entity_type VARCHAR(50);
ALTER TABLE comments ADD COLUMN IF NOT EXISTS entity_id UUID;

-- Step 2: Migrate existing data (set entity_type='issue' and copy issue_id to entity_id)
UPDATE comments
SET entity_type = 'issue',
    entity_id = issue_id
WHERE entity_type IS NULL AND entity_id IS NULL;

-- Step 3: Make new columns NOT NULL after migration
ALTER TABLE comments ALTER COLUMN entity_type SET NOT NULL;
ALTER TABLE comments ALTER COLUMN entity_id SET NOT NULL;

-- Step 4: Drop foreign key constraint on issue_id (if it exists)
DO $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM information_schema.table_constraints
        WHERE constraint_name = 'comments_issue_id_fkey'
          AND table_name = 'comments'
    ) THEN
        ALTER TABLE comments DROP CONSTRAINT comments_issue_id_fkey;
    END IF;
END$$;

-- Step 5: Drop the old issue_id column
ALTER TABLE comments DROP COLUMN IF EXISTS issue_id;

-- Step 6: Create index for performance on entity lookups
CREATE INDEX IF NOT EXISTS idx_comments_entity
ON comments(entity_type, entity_id);

-- Step 7: Create index on created_at for chronological ordering
CREATE INDEX IF NOT EXISTS idx_comments_created_at
ON comments(created_at);

COMMIT;

-- Verification queries (run these manually to verify migration)
-- SELECT entity_type, COUNT(*) as count FROM comments GROUP BY entity_type;
-- SELECT * FROM comments LIMIT 5;
