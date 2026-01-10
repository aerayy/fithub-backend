-- Migration: Ensure clients.user_id has PRIMARY KEY constraint
-- This migration adds PRIMARY KEY constraint if it doesn't exist
-- Required for ON CONFLICT (user_id) to work properly in signup flow
-- Idempotent: safe to run multiple times

-- Check if PRIMARY KEY already exists on user_id column
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 
        FROM pg_constraint c
        JOIN pg_attribute a ON a.attrelid = c.conrelid AND a.attnum = ANY(c.conkey)
        WHERE c.conrelid = 'clients'::regclass
        AND c.contype = 'p'  -- PRIMARY KEY
        AND a.attname = 'user_id'
    ) THEN
        ALTER TABLE clients ADD CONSTRAINT clients_user_id_pk PRIMARY KEY (user_id);
        RAISE NOTICE 'Added PRIMARY KEY constraint clients_user_id_pk on clients.user_id';
    ELSE
        RAISE NOTICE 'PRIMARY KEY constraint already exists on clients.user_id';
    END IF;
EXCEPTION
    WHEN duplicate_object THEN
        RAISE NOTICE 'PRIMARY KEY constraint clients_user_id_pk already exists';
END $$;
