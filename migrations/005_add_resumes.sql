-- Migration: Add resumes and resume_sections tables
-- Description: Support for resume parsing, building, and management
-- Date: 2025-10-16

-- Create resumes table
CREATE TABLE resumes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(200) NOT NULL,
    file_path VARCHAR(500),
    file_type VARCHAR(20) NOT NULL,
    is_primary BOOLEAN NOT NULL DEFAULT FALSE,
    target_role VARCHAR(200),
    target_company VARCHAR(200),
    parsed_data JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Create indexes for resumes
CREATE INDEX idx_resumes_title ON resumes(title);
CREATE INDEX idx_resumes_is_primary ON resumes(is_primary);
CREATE INDEX idx_resumes_target_role ON resumes(target_role);
CREATE INDEX idx_resumes_target_company ON resumes(target_company);

-- Create resume_sections table
CREATE TABLE resume_sections (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    resume_id UUID NOT NULL REFERENCES resumes(id) ON DELETE CASCADE,
    section_type VARCHAR(50) NOT NULL,
    title VARCHAR(200) NOT NULL,
    content TEXT NOT NULL,
    "order" INTEGER NOT NULL DEFAULT 0,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    section_metadata JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Create indexes for resume_sections
CREATE INDEX idx_resume_sections_resume_id ON resume_sections(resume_id);
CREATE INDEX idx_resume_sections_section_type ON resume_sections(section_type);
CREATE INDEX idx_resume_sections_order ON resume_sections("order");

-- Add comments
COMMENT ON TABLE resumes IS 'Stores uploaded and parsed resume data';
COMMENT ON TABLE resume_sections IS 'Reusable content blocks for resumes (experiences, education, projects, etc.)';
COMMENT ON COLUMN resumes.parsed_data IS 'Raw JSON data extracted from resume file via AI';
COMMENT ON COLUMN resume_sections.section_metadata IS 'Section-specific metadata (company, dates, location, etc.)';
COMMENT ON COLUMN resume_sections."order" IS 'Display order for sections within a resume';
