-- Migration: Add career management tables (companies, job_applications, network_contacts)
-- Part of Career Management System initiative (TURBOCODE-I16)

-- Companies table
CREATE TABLE IF NOT EXISTS companies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    website VARCHAR(500),
    industry VARCHAR(100),
    size VARCHAR(50),  -- e.g., "Startup (< 50)", "Medium (50-500)", "Large (500+)"
    location VARCHAR(255),
    remote_policy VARCHAR(50),  -- e.g., "Remote", "Hybrid", "In-Office"

    -- Status tracking
    target_status VARCHAR(50) DEFAULT 'researching',  -- researching, interested, applied, interviewing, offer, accepted, rejected, not_interested
    application_count INTEGER DEFAULT 0,

    -- Research & notes
    research_notes TEXT,
    culture_notes TEXT,
    tech_stack JSONB,  -- Flexible storage for tech stack info
    glassdoor_rating FLOAT,

    -- Contact & social
    linkedin_url VARCHAR(500),
    careers_page_url VARCHAR(500),

    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    -- Constraints
    CONSTRAINT companies_target_status_check CHECK (
        target_status IN (
            'researching', 'interested', 'applied', 'interviewing',
            'offer', 'accepted', 'rejected', 'not_interested'
        )
    )
);

-- Job applications table
CREATE TABLE IF NOT EXISTS job_applications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Foreign keys
    company_id UUID REFERENCES companies(id) ON DELETE CASCADE,
    resume_id UUID REFERENCES resumes(id) ON DELETE SET NULL,
    project_id UUID REFERENCES projects(id) ON DELETE SET NULL,  -- Optional: portfolio project used

    -- Job details
    job_title VARCHAR(255) NOT NULL,
    job_description TEXT,
    job_url VARCHAR(500),
    salary_min INTEGER,
    salary_max INTEGER,
    location VARCHAR(255),
    remote_policy VARCHAR(50),

    -- Application status
    status VARCHAR(50) DEFAULT 'researching',  -- researching, interested, applied, screening, phone_screen, technical_interview, onsite, offer, negotiating, accepted, rejected, withdrawn, ghosted
    application_date TIMESTAMP WITH TIME ZONE,
    last_contact_date TIMESTAMP WITH TIME ZONE,
    next_followup_date TIMESTAMP WITH TIME ZONE,

    -- Application materials
    cover_letter_id UUID REFERENCES documents(id) ON DELETE SET NULL,
    resume_version VARCHAR(50),  -- Track which version was sent

    -- Tracking
    source VARCHAR(100),  -- e.g., "LinkedIn", "Indeed", "Referral", "Company Website"
    referrer_contact_id UUID,  -- Will link to network_contacts after that table exists

    -- Interview tracking
    interview_count INTEGER DEFAULT 0,
    interview_notes TEXT,

    -- Response tracking
    response_time_hours INTEGER,  -- Time from application to first response
    rejection_reason TEXT,

    -- Metadata
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    -- Constraints
    CONSTRAINT job_applications_status_check CHECK (
        status IN (
            'researching', 'interested', 'applied', 'screening',
            'phone_screen', 'technical_interview', 'onsite', 'offer',
            'negotiating', 'accepted', 'rejected', 'withdrawn', 'ghosted'
        )
    )
);

-- Network contacts table
CREATE TABLE IF NOT EXISTS network_contacts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Foreign keys
    company_id UUID REFERENCES companies(id) ON DELETE SET NULL,  -- Optional: may not be at a company we're tracking

    -- Contact info
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    email VARCHAR(255),
    linkedin_url VARCHAR(500),
    phone VARCHAR(50),

    -- Professional info
    current_title VARCHAR(255),
    current_company VARCHAR(255),  -- Text field for companies not in our companies table

    -- Contact type
    contact_type VARCHAR(50),  -- recruiter_internal, recruiter_external, hiring_manager, peer, referrer, mentor, former_colleague

    -- Relationship tracking
    relationship_strength VARCHAR(20) DEFAULT 'cold',  -- cold, warm, hot
    last_contact_date TIMESTAMP WITH TIME ZONE,
    next_followup_date TIMESTAMP WITH TIME ZONE,
    interaction_count INTEGER DEFAULT 0,

    -- Context
    how_we_met TEXT,
    conversation_history TEXT,
    referral_status VARCHAR(50),  -- none, requested, agreed, completed

    -- Social
    github_url VARCHAR(500),
    personal_website VARCHAR(500),
    twitter_url VARCHAR(500),

    -- Metadata
    notes TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    -- Constraints
    CONSTRAINT network_contacts_contact_type_check CHECK (
        contact_type IN (
            'recruiter_internal', 'recruiter_external', 'hiring_manager',
            'peer', 'referrer', 'mentor', 'former_colleague'
        )
    ),
    CONSTRAINT network_contacts_relationship_strength_check CHECK (
        relationship_strength IN ('cold', 'warm', 'hot')
    ),
    CONSTRAINT network_contacts_referral_status_check CHECK (
        referral_status IN ('none', 'requested', 'agreed', 'completed')
    )
);

-- Add foreign key for referrer_contact_id now that network_contacts exists
ALTER TABLE job_applications
ADD CONSTRAINT job_applications_referrer_fkey
FOREIGN KEY (referrer_contact_id) REFERENCES network_contacts(id) ON DELETE SET NULL;

-- Association table: company_tags
CREATE TABLE IF NOT EXISTS company_tags (
    company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    tag_id UUID NOT NULL REFERENCES tags(id) ON DELETE CASCADE,
    PRIMARY KEY (company_id, tag_id)
);

-- Association table: job_application_tags
CREATE TABLE IF NOT EXISTS job_application_tags (
    job_application_id UUID NOT NULL REFERENCES job_applications(id) ON DELETE CASCADE,
    tag_id UUID NOT NULL REFERENCES tags(id) ON DELETE CASCADE,
    PRIMARY KEY (job_application_id, tag_id)
);

-- Association table: network_contact_tags
CREATE TABLE IF NOT EXISTS network_contact_tags (
    network_contact_id UUID NOT NULL REFERENCES network_contacts(id) ON DELETE CASCADE,
    tag_id UUID NOT NULL REFERENCES tags(id) ON DELETE CASCADE,
    PRIMARY KEY (network_contact_id, tag_id)
);

-- Indexes for performance

-- Companies indexes
CREATE INDEX IF NOT EXISTS idx_companies_target_status ON companies(target_status);
CREATE INDEX IF NOT EXISTS idx_companies_industry ON companies(industry);
CREATE INDEX IF NOT EXISTS idx_companies_name ON companies(name);
CREATE INDEX IF NOT EXISTS idx_companies_created_at ON companies(created_at);

-- Job applications indexes
CREATE INDEX IF NOT EXISTS idx_job_applications_company_id ON job_applications(company_id);
CREATE INDEX IF NOT EXISTS idx_job_applications_resume_id ON job_applications(resume_id);
CREATE INDEX IF NOT EXISTS idx_job_applications_project_id ON job_applications(project_id);
CREATE INDEX IF NOT EXISTS idx_job_applications_status ON job_applications(status);
CREATE INDEX IF NOT EXISTS idx_job_applications_application_date ON job_applications(application_date);
CREATE INDEX IF NOT EXISTS idx_job_applications_next_followup_date ON job_applications(next_followup_date);
CREATE INDEX IF NOT EXISTS idx_job_applications_source ON job_applications(source);
CREATE INDEX IF NOT EXISTS idx_job_applications_created_at ON job_applications(created_at);

-- Network contacts indexes
CREATE INDEX IF NOT EXISTS idx_network_contacts_company_id ON network_contacts(company_id);
CREATE INDEX IF NOT EXISTS idx_network_contacts_contact_type ON network_contacts(contact_type);
CREATE INDEX IF NOT EXISTS idx_network_contacts_relationship_strength ON network_contacts(relationship_strength);
CREATE INDEX IF NOT EXISTS idx_network_contacts_last_contact_date ON network_contacts(last_contact_date);
CREATE INDEX IF NOT EXISTS idx_network_contacts_next_followup_date ON network_contacts(next_followup_date);
CREATE INDEX IF NOT EXISTS idx_network_contacts_email ON network_contacts(email);
CREATE INDEX IF NOT EXISTS idx_network_contacts_is_active ON network_contacts(is_active) WHERE is_active = TRUE;
CREATE INDEX IF NOT EXISTS idx_network_contacts_created_at ON network_contacts(created_at);

-- Association table indexes (for reverse lookups)
CREATE INDEX IF NOT EXISTS idx_company_tags_tag_id ON company_tags(tag_id);
CREATE INDEX IF NOT EXISTS idx_job_application_tags_tag_id ON job_application_tags(tag_id);
CREATE INDEX IF NOT EXISTS idx_network_contact_tags_tag_id ON network_contact_tags(tag_id);

-- Comments
COMMENT ON TABLE companies IS 'Companies for job search tracking and research';
COMMENT ON TABLE job_applications IS 'Job applications with status tracking, materials, and interview history';
COMMENT ON TABLE network_contacts IS 'Professional network contacts for job search and referrals';

COMMENT ON COLUMN companies.tech_stack IS 'JSONB field for flexible storage of technology stack information';
COMMENT ON COLUMN companies.target_status IS 'Current status of company in job search funnel';
COMMENT ON COLUMN job_applications.resume_version IS 'Identifier for which resume version was used for this application';
COMMENT ON COLUMN job_applications.response_time_hours IS 'Hours from application submission to first company response';
COMMENT ON COLUMN network_contacts.relationship_strength IS 'Strength of professional relationship: cold (no prior contact), warm (some interaction), hot (strong connection)';
COMMENT ON COLUMN network_contacts.referral_status IS 'Status of referral request: none, requested, agreed, completed';
