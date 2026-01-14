-- Migration: Add status and metadata to documents table
-- Description: Add status tracking and structured metadata for document maintenance
-- Date: 2025-10-20

-- Add status field with default value
ALTER TABLE documents
ADD COLUMN IF NOT EXISTS status VARCHAR(20) NOT NULL DEFAULT 'draft';

-- Add index on status for filtering
CREATE INDEX IF NOT EXISTS idx_documents_status ON documents(status);

-- Add doc_metadata JSONB field for structured information (not 'metadata' - reserved by SQLAlchemy)
ALTER TABLE documents
ADD COLUMN IF NOT EXISTS doc_metadata JSONB DEFAULT '{}'::jsonb;

-- Comment explaining the fields
COMMENT ON COLUMN documents.status IS 'Document lifecycle status: draft, in_review, approved, published, archived';
COMMENT ON COLUMN documents.doc_metadata IS 'Structured metadata (owner, update_frequency, review_cycle, etc.) - prevents metadata from cluttering document body';

-- Update existing documents to have empty metadata
UPDATE documents SET doc_metadata = '{}'::jsonb WHERE doc_metadata IS NULL;
