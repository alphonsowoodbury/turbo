-- Migration: Add conversation memory and summary tables
-- Description: Add long-term conversation memory system with semantic search and summaries
-- Date: 2025-10-20

-- Create conversation_memories table for long-term memory storage
CREATE TABLE IF NOT EXISTS conversation_memories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Polymorphic entity reference (staff or mentor)
    entity_type VARCHAR(20) NOT NULL,
    entity_id UUID NOT NULL,

    -- Memory content
    memory_type VARCHAR(50) NOT NULL,  -- fact, preference, decision, insight, entity_mention
    content TEXT NOT NULL,

    -- Importance and relevance scoring
    importance FLOAT NOT NULL DEFAULT 0.5,
    relevance_score FLOAT NOT NULL DEFAULT 1.0,

    -- Related entities mentioned in this memory
    entities_mentioned JSONB,

    -- Vector embedding for semantic search (384 dimensions for all-MiniLM-L6-v2)
    embedding FLOAT[384],

    -- Source tracking
    source_message_ids TEXT[],  -- Array of message UUIDs

    -- Temporal metadata
    first_mentioned_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_accessed_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    access_count INTEGER NOT NULL DEFAULT 0,

    -- Standard timestamps
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    -- Constraints
    CONSTRAINT chk_importance_range CHECK (importance >= 0.0 AND importance <= 1.0),
    CONSTRAINT chk_relevance_range CHECK (relevance_score >= 0.0 AND relevance_score <= 1.0),
    CONSTRAINT chk_access_count CHECK (access_count >= 0)
);

-- Create indexes for conversation_memories
CREATE INDEX IF NOT EXISTS idx_conversation_memories_entity ON conversation_memories(entity_type, entity_id);
CREATE INDEX IF NOT EXISTS idx_conversation_memories_type ON conversation_memories(memory_type);
CREATE INDEX IF NOT EXISTS idx_conversation_memories_importance ON conversation_memories(importance DESC);
CREATE INDEX IF NOT EXISTS idx_conversation_memories_relevance ON conversation_memories(relevance_score DESC);
CREATE INDEX IF NOT EXISTS idx_conversation_memories_first_mentioned ON conversation_memories(first_mentioned_at DESC);

-- Create conversation_summaries table for message range summaries
CREATE TABLE IF NOT EXISTS conversation_summaries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Polymorphic entity reference (staff or mentor)
    entity_type VARCHAR(20) NOT NULL,
    entity_id UUID NOT NULL,

    -- Summary content
    summary_text TEXT NOT NULL,

    -- Message range this summary covers
    message_range_start INTEGER NOT NULL,
    message_range_end INTEGER NOT NULL,
    message_count INTEGER NOT NULL,

    -- Extracted information
    key_topics TEXT[],  -- Array of key topics discussed
    entities_discussed JSONB,  -- {issues: [uuid1], projects: [], documents: []}
    decisions_made TEXT[],  -- Array of decisions made

    -- Vector embedding for semantic search
    embedding FLOAT[384],

    -- Time range covered by this summary
    time_range_start TIMESTAMP,
    time_range_end TIMESTAMP,

    -- Standard timestamps
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    -- Constraints
    CONSTRAINT chk_message_range CHECK (message_range_end >= message_range_start),
    CONSTRAINT chk_message_count CHECK (message_count > 0),
    CONSTRAINT chk_time_range CHECK (time_range_end IS NULL OR time_range_start IS NULL OR time_range_end >= time_range_start)
);

-- Create indexes for conversation_summaries
CREATE INDEX IF NOT EXISTS idx_conversation_summaries_entity ON conversation_summaries(entity_type, entity_id);
CREATE INDEX IF NOT EXISTS idx_conversation_summaries_range ON conversation_summaries(message_range_start, message_range_end);
CREATE INDEX IF NOT EXISTS idx_conversation_summaries_created ON conversation_summaries(created_at DESC);

-- Create unique constraint to prevent duplicate summaries for the same range
CREATE UNIQUE INDEX IF NOT EXISTS idx_conversation_summaries_unique_range
ON conversation_summaries(entity_type, entity_id, message_range_start, message_range_end);

-- Comments explaining the tables and fields
COMMENT ON TABLE conversation_memories IS 'Long-term memory storage for AI conversations with semantic search capabilities';
COMMENT ON TABLE conversation_summaries IS 'Summaries of conversation message ranges for efficient context loading';

COMMENT ON COLUMN conversation_memories.entity_type IS 'Type of entity: staff or mentor';
COMMENT ON COLUMN conversation_memories.entity_id IS 'UUID of the staff member or mentor';
COMMENT ON COLUMN conversation_memories.memory_type IS 'Type of memory: fact, preference, decision, insight, entity_mention';
COMMENT ON COLUMN conversation_memories.content IS 'The memory content - clear, concise description';
COMMENT ON COLUMN conversation_memories.importance IS 'Importance score 0.0-1.0: 0.8-1.0 (critical), 0.5-0.7 (important), 0.3-0.4 (contextual)';
COMMENT ON COLUMN conversation_memories.relevance_score IS 'Relevance score with temporal decay, starts at 1.0';
COMMENT ON COLUMN conversation_memories.entities_mentioned IS 'JSON of related entities: {issues: [uuid], projects: [], documents: []}';
COMMENT ON COLUMN conversation_memories.embedding IS '384-dimensional vector for semantic search using all-MiniLM-L6-v2';
COMMENT ON COLUMN conversation_memories.source_message_ids IS 'Array of message UUIDs where this memory originated';
COMMENT ON COLUMN conversation_memories.first_mentioned_at IS 'When this memory was first mentioned';
COMMENT ON COLUMN conversation_memories.last_accessed_at IS 'Last time this memory was retrieved and used';
COMMENT ON COLUMN conversation_memories.access_count IS 'Number of times this memory has been accessed';

COMMENT ON COLUMN conversation_summaries.summary_text IS 'Concise 2-3 paragraph summary of the conversation segment';
COMMENT ON COLUMN conversation_summaries.message_range_start IS 'Starting message index (inclusive)';
COMMENT ON COLUMN conversation_summaries.message_range_end IS 'Ending message index (inclusive)';
COMMENT ON COLUMN conversation_summaries.message_count IS 'Number of messages in this summary';
COMMENT ON COLUMN conversation_summaries.key_topics IS 'Array of 2-5 key topics discussed in this segment';
COMMENT ON COLUMN conversation_summaries.entities_discussed IS 'JSON of entities mentioned: {issues: [uuid], projects: [], documents: []}';
COMMENT ON COLUMN conversation_summaries.decisions_made IS 'Array of key decisions made in this segment';
COMMENT ON COLUMN conversation_summaries.embedding IS '384-dimensional vector for semantic search';
COMMENT ON COLUMN conversation_summaries.time_range_start IS 'Timestamp of first message in summary';
COMMENT ON COLUMN conversation_summaries.time_range_end IS 'Timestamp of last message in summary';
