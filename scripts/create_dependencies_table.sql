-- Create issue_dependencies table
CREATE TABLE IF NOT EXISTS issue_dependencies (
    blocking_issue_id UUID NOT NULL,
    blocked_issue_id UUID NOT NULL,
    dependency_type VARCHAR(50) DEFAULT 'blocks',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (blocking_issue_id, blocked_issue_id),
    FOREIGN KEY (blocking_issue_id) REFERENCES issues(id) ON DELETE CASCADE,
    FOREIGN KEY (blocked_issue_id) REFERENCES issues(id) ON DELETE CASCADE,
    CONSTRAINT no_self_dependency CHECK (blocking_issue_id <> blocked_issue_id)
);

-- Create indexes for efficient queries
CREATE INDEX IF NOT EXISTS idx_issue_dependencies_blocking ON issue_dependencies(blocking_issue_id);
CREATE INDEX IF NOT EXISTS idx_issue_dependencies_blocked ON issue_dependencies(blocked_issue_id);

-- Show table structure
\d issue_dependencies