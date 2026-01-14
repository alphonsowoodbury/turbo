-- Migration: Add work experiences and achievement facts tables
-- Part of Career Management System - Work History tracking

-- Work experiences table
CREATE TABLE IF NOT EXISTS work_experiences (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Foreign keys
    company_id UUID REFERENCES companies(id) ON DELETE SET NULL,

    -- Role details
    role_title VARCHAR(255) NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE,
    is_current BOOLEAN DEFAULT FALSE,

    -- Team context (flexible JSONB for complex structures)
    team_context JSONB,  -- team_size, reporting_to, cross_functional_teams, etc.

    -- Technologies used (array of tech names or skill references)
    technologies JSONB,

    -- Additional context
    location VARCHAR(255),
    employment_type VARCHAR(50),  -- full_time, part_time, contract, freelance
    department VARCHAR(100),

    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    -- Constraints
    CONSTRAINT work_experiences_employment_type_check CHECK (
        employment_type IN ('full_time', 'part_time', 'contract', 'freelance')
    ),
    CONSTRAINT work_experiences_dates_check CHECK (
        end_date IS NULL OR end_date >= start_date
    ),
    CONSTRAINT work_experiences_current_check CHECK (
        (is_current = TRUE AND end_date IS NULL) OR (is_current = FALSE)
    )
);

-- Achievement facts table - granular, atomic facts about accomplishments
CREATE TABLE IF NOT EXISTS achievement_facts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Foreign keys
    experience_id UUID NOT NULL REFERENCES work_experiences(id) ON DELETE CASCADE,

    -- The core factual statement
    fact_text TEXT NOT NULL,

    -- Quantifiable metrics
    metric_type VARCHAR(50),  -- cost_savings, time_reduction, scale, performance_improvement, team_size, etc.
    metric_value NUMERIC(15, 2),
    metric_unit VARCHAR(50),  -- percentage, dollars, days, gigabytes_daily, users, requests_per_second, etc.

    -- Multi-dimensional tagging for extraction
    dimensions JSONB NOT NULL DEFAULT '[]'::jsonb,  -- Array: ["leadership", "technical", "cost_optimization", "innovation"]

    -- Amazon Leadership Principles mapping (optional)
    leadership_principles JSONB DEFAULT '[]'::jsonb,  -- Array: ["frugality", "bias_for_action", "deliver_results"]

    -- Skills demonstrated/used
    skills_used JSONB DEFAULT '[]'::jsonb,  -- Array of skill names or IDs

    -- STAR components (for LP story generation)
    context TEXT,  -- Situation/Task context
    impact TEXT,   -- Result/Impact on business/team

    -- Ordering within experience
    display_order INTEGER DEFAULT 0,

    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    -- Constraints
    CONSTRAINT achievement_facts_metric_value_check CHECK (
        metric_value IS NULL OR metric_value >= 0
    )
);

-- Association table: work_experience_tags
CREATE TABLE IF NOT EXISTS work_experience_tags (
    work_experience_id UUID NOT NULL REFERENCES work_experiences(id) ON DELETE CASCADE,
    tag_id UUID NOT NULL REFERENCES tags(id) ON DELETE CASCADE,
    PRIMARY KEY (work_experience_id, tag_id)
);

-- Association table: achievement_fact_tags
CREATE TABLE IF NOT EXISTS achievement_fact_tags (
    achievement_fact_id UUID NOT NULL REFERENCES achievement_facts(id) ON DELETE CASCADE,
    tag_id UUID NOT NULL REFERENCES tags(id) ON DELETE CASCADE,
    PRIMARY KEY (achievement_fact_id, tag_id)
);

-- Indexes for performance

-- Work experiences indexes
CREATE INDEX IF NOT EXISTS idx_work_experiences_company_id ON work_experiences(company_id);
CREATE INDEX IF NOT EXISTS idx_work_experiences_start_date ON work_experiences(start_date DESC);
CREATE INDEX IF NOT EXISTS idx_work_experiences_end_date ON work_experiences(end_date DESC NULLS FIRST);
CREATE INDEX IF NOT EXISTS idx_work_experiences_is_current ON work_experiences(is_current) WHERE is_current = TRUE;
CREATE INDEX IF NOT EXISTS idx_work_experiences_employment_type ON work_experiences(employment_type);
CREATE INDEX IF NOT EXISTS idx_work_experiences_created_at ON work_experiences(created_at);

-- Achievement facts indexes
CREATE INDEX IF NOT EXISTS idx_achievement_facts_experience_id ON achievement_facts(experience_id);
CREATE INDEX IF NOT EXISTS idx_achievement_facts_metric_type ON achievement_facts(metric_type);
CREATE INDEX IF NOT EXISTS idx_achievement_facts_display_order ON achievement_facts(experience_id, display_order);

-- JSONB indexes for efficient querying of arrays
CREATE INDEX IF NOT EXISTS idx_achievement_facts_dimensions ON achievement_facts USING GIN (dimensions);
CREATE INDEX IF NOT EXISTS idx_achievement_facts_leadership_principles ON achievement_facts USING GIN (leadership_principles);
CREATE INDEX IF NOT EXISTS idx_achievement_facts_skills_used ON achievement_facts USING GIN (skills_used);

-- Association table indexes
CREATE INDEX IF NOT EXISTS idx_work_experience_tags_tag_id ON work_experience_tags(tag_id);
CREATE INDEX IF NOT EXISTS idx_achievement_fact_tags_tag_id ON achievement_fact_tags(tag_id);

-- Full-text search index on achievement facts
CREATE INDEX IF NOT EXISTS idx_achievement_facts_fact_text_fts ON achievement_facts USING GIN (to_tsvector('english', fact_text));
CREATE INDEX IF NOT EXISTS idx_achievement_facts_context_fts ON achievement_facts USING GIN (to_tsvector('english', COALESCE(context, '')));
CREATE INDEX IF NOT EXISTS idx_achievement_facts_impact_fts ON achievement_facts USING GIN (to_tsvector('english', COALESCE(impact, '')));

-- Comments
COMMENT ON TABLE work_experiences IS 'Work history and employment experiences with role details';
COMMENT ON TABLE achievement_facts IS 'Granular, atomic facts about accomplishments - prevents AI hallucination through factual precision';

COMMENT ON COLUMN work_experiences.team_context IS 'JSONB field for flexible team structure data (team_size, reporting_to, cross_functional_teams, etc.)';
COMMENT ON COLUMN work_experiences.technologies IS 'JSONB array of technologies/tools used in this role';
COMMENT ON COLUMN achievement_facts.fact_text IS 'Core factual statement - atomic, verifiable, quantifiable';
COMMENT ON COLUMN achievement_facts.dimensions IS 'JSONB array of dimensional tags for multi-aspect extraction (leadership, technical, customer_obsession, etc.)';
COMMENT ON COLUMN achievement_facts.leadership_principles IS 'JSONB array of Amazon Leadership Principles demonstrated (frugality, bias_for_action, etc.)';
COMMENT ON COLUMN achievement_facts.skills_used IS 'JSONB array of skills demonstrated in this achievement';
COMMENT ON COLUMN achievement_facts.context IS 'Situation/Task context for STAR format story generation';
COMMENT ON COLUMN achievement_facts.impact IS 'Result/Impact for STAR format story generation';
COMMENT ON COLUMN achievement_facts.metric_type IS 'Type of quantifiable metric (cost_savings, time_reduction, scale, etc.)';
COMMENT ON COLUMN achievement_facts.metric_value IS 'Numerical value of the metric';
COMMENT ON COLUMN achievement_facts.metric_unit IS 'Unit of measurement (percentage, dollars, days, etc.)';
