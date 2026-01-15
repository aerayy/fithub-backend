-- Migration: Add services column to coach_packages table
-- This migration is idempotent - safe to run multiple times

DO $$
BEGIN
    -- Check if services column already exists
    IF NOT EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_schema = 'public' 
        AND table_name = 'coach_packages' 
        AND column_name = 'services'
    ) THEN
        -- Add services column as TEXT[] with default empty array
        ALTER TABLE public.coach_packages 
        ADD COLUMN services TEXT[] NOT NULL DEFAULT '{}'::text[];
        
        RAISE NOTICE 'Added services column to coach_packages table';
    ELSE
        RAISE NOTICE 'services column already exists in coach_packages table';
    END IF;
END $$;
