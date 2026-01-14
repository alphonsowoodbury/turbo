-- Migration: Register Claude Code Service Webhook
-- Description: Registers webhook for autonomous issue implementation via Claude Code CLI
-- Created: 2025-10-20

-- Insert webhook registration for Claude Code service
INSERT INTO webhooks (
    id,
    name,
    url,
    secret,
    events,
    is_active,
    max_retries,
    timeout_seconds,
    headers,
    created_at,
    updated_at
) VALUES (
    gen_random_uuid(),
    'Claude Code Autonomous Implementation',
    'http://claude-code:9000/webhook/issue-assigned',
    'turbo-webhook-secret-change-me',
    '["issue.assigned"]'::jsonb,
    true,
    3,
    300,  -- 5 minute timeout for Claude Code execution
    '{"Content-Type": "application/json"}'::jsonb,
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
) ON CONFLICT DO NOTHING;

-- Create index on webhook events for faster lookups
CREATE INDEX IF NOT EXISTS idx_webhooks_events ON webhooks USING gin (events);
CREATE INDEX IF NOT EXISTS idx_webhooks_active ON webhooks (is_active) WHERE is_active = true;
