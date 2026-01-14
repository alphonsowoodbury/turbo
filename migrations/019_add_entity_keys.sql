-- Migration: Add entity keys system
-- Date: 2025-10-22
-- Description: Adds human-readable keys (CNTXT-1, TURBO-42) to projects, issues, milestones, initiatives, and documents

-- ==========================================
-- 1. CREATE COUNTER TABLE
-- ==========================================
CREATE TABLE IF NOT EXISTS project_entity_counters (
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    entity_type VARCHAR(20) NOT NULL,
    next_number INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (project_id, entity_type)
);

CREATE INDEX idx_entity_counters_project ON project_entity_counters(project_id);

-- ==========================================
-- 2. ADD KEY COLUMNS TO ALL TABLES
-- ==========================================

-- Projects: Add project_key
ALTER TABLE projects ADD COLUMN IF NOT EXISTS project_key VARCHAR(10);
CREATE UNIQUE INDEX IF NOT EXISTS idx_projects_key ON projects(project_key);

-- Issues: Add issue_key and issue_number
ALTER TABLE issues ADD COLUMN IF NOT EXISTS issue_key VARCHAR(20);
ALTER TABLE issues ADD COLUMN IF NOT EXISTS issue_number INTEGER;
CREATE UNIQUE INDEX IF NOT EXISTS idx_issues_key ON issues(issue_key);

-- Milestones: Add milestone_key and milestone_number
ALTER TABLE milestones ADD COLUMN IF NOT EXISTS milestone_key VARCHAR(20);
ALTER TABLE milestones ADD COLUMN IF NOT EXISTS milestone_number INTEGER;
CREATE UNIQUE INDEX IF NOT EXISTS idx_milestones_key ON milestones(milestone_key);

-- Initiatives: Add initiative_key and initiative_number
ALTER TABLE initiatives ADD COLUMN IF NOT EXISTS initiative_key VARCHAR(20);
ALTER TABLE initiatives ADD COLUMN IF NOT EXISTS initiative_number INTEGER;
CREATE UNIQUE INDEX IF NOT EXISTS idx_initiatives_key ON initiatives(initiative_key);

-- Documents: Add document_key and document_number
ALTER TABLE documents ADD COLUMN IF NOT EXISTS document_key VARCHAR(20);
ALTER TABLE documents ADD COLUMN IF NOT EXISTS document_number INTEGER;
CREATE UNIQUE INDEX IF NOT EXISTS idx_documents_key ON documents(document_key);

-- ==========================================
-- 3. BACKFILL EXISTING DATA
-- ==========================================

-- Generate project keys from names (uppercase first 4-6 letters, or abbreviation)
-- This is a simple heuristic - may need manual adjustment
DO $$
DECLARE
    proj RECORD;
    key_candidate TEXT;
    key_final TEXT;
    counter INT;
BEGIN
    FOR proj IN SELECT id, name FROM projects WHERE project_key IS NULL ORDER BY created_at
    LOOP
        -- Generate key from first letters of words or first 5 chars
        key_candidate := UPPER(REGEXP_REPLACE(
            SUBSTRING(
                REGEXP_REPLACE(proj.name, '[^a-zA-Z0-9 ]', '', 'g'),
                1, 10
            ),
            ' +', '', 'g'
        ));

        -- Ensure at least 2 chars
        IF LENGTH(key_candidate) < 2 THEN
            key_candidate := UPPER(SUBSTRING(REGEXP_REPLACE(proj.name, '[^a-zA-Z0-9]', '', 'g'), 1, 5));
        END IF;

        -- Make unique by adding numbers if needed
        key_final := key_candidate;
        counter := 1;
        WHILE EXISTS (SELECT 1 FROM projects WHERE project_key = key_final) LOOP
            key_final := key_candidate || counter;
            counter := counter + 1;
        END LOOP;

        UPDATE projects SET project_key = key_final WHERE id = proj.id;
    END LOOP;
END $$;

-- Backfill issues with keys
DO $$
DECLARE
    iss RECORD;
    proj_key TEXT;
    iss_num INT;
BEGIN
    FOR iss IN SELECT i.id, i.project_id FROM issues i WHERE i.issue_key IS NULL ORDER BY i.created_at
    LOOP
        -- Get project key
        SELECT project_key INTO proj_key FROM projects WHERE id = iss.project_id;

        IF proj_key IS NULL THEN
            CONTINUE;  -- Skip issues without projects
        END IF;

        -- Get or create counter
        INSERT INTO project_entity_counters (project_id, entity_type, next_number)
        VALUES (iss.project_id, 'issue', 1)
        ON CONFLICT (project_id, entity_type) DO NOTHING;

        -- Get next number and increment
        SELECT next_number INTO iss_num FROM project_entity_counters
        WHERE project_id = iss.project_id AND entity_type = 'issue'
        FOR UPDATE;

        UPDATE project_entity_counters
        SET next_number = next_number + 1
        WHERE project_id = iss.project_id AND entity_type = 'issue';

        -- Update issue
        UPDATE issues
        SET issue_key = proj_key || '-' || iss_num,
            issue_number = iss_num
        WHERE id = iss.id;
    END LOOP;
END $$;

-- Backfill milestones with keys
DO $$
DECLARE
    mile RECORD;
    proj_key TEXT;
    mile_num INT;
BEGIN
    FOR mile IN SELECT m.id, m.project_id FROM milestones m WHERE m.milestone_key IS NULL ORDER BY m.created_at
    LOOP
        SELECT project_key INTO proj_key FROM projects WHERE id = mile.project_id;

        IF proj_key IS NULL THEN
            CONTINUE;
        END IF;

        INSERT INTO project_entity_counters (project_id, entity_type, next_number)
        VALUES (mile.project_id, 'milestone', 1)
        ON CONFLICT (project_id, entity_type) DO NOTHING;

        SELECT next_number INTO mile_num FROM project_entity_counters
        WHERE project_id = mile.project_id AND entity_type = 'milestone'
        FOR UPDATE;

        UPDATE project_entity_counters
        SET next_number = next_number + 1
        WHERE project_id = mile.project_id AND entity_type = 'milestone';

        UPDATE milestones
        SET milestone_key = proj_key || '-M' || mile_num,
            milestone_number = mile_num
        WHERE id = mile.id;
    END LOOP;
END $$;

-- Backfill initiatives with keys
DO $$
DECLARE
    init RECORD;
    proj_key TEXT;
    init_num INT;
BEGIN
    FOR init IN SELECT i.id, i.project_id FROM initiatives i WHERE i.initiative_key IS NULL ORDER BY i.created_at
    LOOP
        IF init.project_id IS NULL THEN
            CONTINUE;  -- Skip cross-project initiatives for now
        END IF;

        SELECT project_key INTO proj_key FROM projects WHERE id = init.project_id;

        IF proj_key IS NULL THEN
            CONTINUE;
        END IF;

        INSERT INTO project_entity_counters (project_id, entity_type, next_number)
        VALUES (init.project_id, 'initiative', 1)
        ON CONFLICT (project_id, entity_type) DO NOTHING;

        SELECT next_number INTO init_num FROM project_entity_counters
        WHERE project_id = init.project_id AND entity_type = 'initiative'
        FOR UPDATE;

        UPDATE project_entity_counters
        SET next_number = next_number + 1
        WHERE project_id = init.project_id AND entity_type = 'initiative';

        UPDATE initiatives
        SET initiative_key = proj_key || '-I' || init_num,
            initiative_number = init_num
        WHERE id = init.id;
    END LOOP;
END $$;

-- Backfill documents with keys
DO $$
DECLARE
    doc RECORD;
    proj_key TEXT;
    doc_num INT;
BEGIN
    FOR doc IN SELECT d.id, d.project_id FROM documents d WHERE d.document_key IS NULL ORDER BY d.created_at
    LOOP
        SELECT project_key INTO proj_key FROM projects WHERE id = doc.project_id;

        IF proj_key IS NULL THEN
            CONTINUE;
        END IF;

        INSERT INTO project_entity_counters (project_id, entity_type, next_number)
        VALUES (doc.project_id, 'document', 1)
        ON CONFLICT (project_id, entity_type) DO NOTHING;

        SELECT next_number INTO doc_num FROM project_entity_counters
        WHERE project_id = doc.project_id AND entity_type = 'document'
        FOR UPDATE;

        UPDATE project_entity_counters
        SET next_number = next_number + 1
        WHERE project_id = doc.project_id AND entity_type = 'document';

        UPDATE documents
        SET document_key = proj_key || '-D' || doc_num,
            document_number = doc_num
        WHERE id = doc.id;
    END LOOP;
END $$;

-- ==========================================
-- 4. MAKE COLUMNS NOT NULL (after backfill)
-- ==========================================
-- Note: Issues and Initiatives keys are nullable because:
-- - Discovery issues may not have a project_id
-- - Initiatives may be cross-project (no single project_id)

ALTER TABLE projects ALTER COLUMN project_key SET NOT NULL;
-- Issues: Keys are nullable for discovery issues without project_id
-- ALTER TABLE issues ALTER COLUMN issue_key SET NOT NULL;
-- ALTER TABLE issues ALTER COLUMN issue_number SET NOT NULL;
ALTER TABLE milestones ALTER COLUMN milestone_key SET NOT NULL;
ALTER TABLE milestones ALTER COLUMN milestone_number SET NOT NULL;
-- Initiatives: Keys are nullable for cross-project initiatives
-- ALTER TABLE initiatives ALTER COLUMN initiative_key SET NOT NULL;
-- ALTER TABLE initiatives ALTER COLUMN initiative_number SET NOT NULL;
ALTER TABLE documents ALTER COLUMN document_key SET NOT NULL;
ALTER TABLE documents ALTER COLUMN document_number SET NOT NULL;

-- ==========================================
-- VERIFICATION
-- ==========================================
-- Check that all entities have keys
-- SELECT COUNT(*) FROM projects WHERE project_key IS NULL;
-- SELECT COUNT(*) FROM issues WHERE issue_key IS NULL;
-- SELECT COUNT(*) FROM milestones WHERE milestone_key IS NULL;
-- SELECT COUNT(*) FROM initiatives WHERE initiative_key IS NULL;
-- SELECT COUNT(*) FROM documents WHERE document_key IS NULL;
