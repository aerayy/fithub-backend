-- Migration: Ensure clients.user_id has unique constraint
-- This migration is idempotent - it will only add the constraint if it doesn't exist
-- Note: This assumes user_id is already a PRIMARY KEY, but adds explicit unique constraint
-- for ON CONFLICT (user_id) to work properly

-- Check if constraint exists before adding (PostgreSQL 9.5+)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 
        FROM pg_constraint 
        WHERE conname = 'clients_user_id_key' 
        AND conrelid = 'clients'::regclass
    ) THEN
        -- Add unique constraint if primary key constraint doesn't already provide uniqueness
        ALTER TABLE clients ADD CONSTRAINT clients_user_id_key UNIQUE (user_id);
    END IF;
END $$;

-- Alternative: If user_id is already PRIMARY KEY, the unique constraint is implicit
-- This migration is safe to run multiple times
