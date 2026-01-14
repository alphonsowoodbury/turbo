-- Migration: Add role_title column to staff table (SQLite version)
-- Date: 2025-10-21
-- Description: Add role_title field to support various staff roles (Board Member, Advisor, etc.)

BEGIN;

-- Add role_title column
ALTER TABLE staff ADD COLUMN role_title VARCHAR(100);

-- Create index for faster queries
CREATE INDEX IF NOT EXISTS idx_staff_role_title ON staff(role_title);

COMMIT;
