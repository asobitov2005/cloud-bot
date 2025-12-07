-- Migration: Add blocked_at column to users table
-- Date: 2025-12-07

-- Add the blocked_at column
ALTER TABLE users ADD COLUMN IF NOT EXISTS blocked_at TIMESTAMP;

-- Backfill: Set blocked_at to joined_at for currently blocked users
-- This is an approximation since we don't have historical block data
UPDATE users 
SET blocked_at = joined_at 
WHERE is_blocked = true AND blocked_at IS NULL;

-- Comment: This column tracks when a user was blocked for accurate statistics
COMMENT ON COLUMN users.blocked_at IS 'Timestamp when the user was blocked';
