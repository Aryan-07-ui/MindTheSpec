-- MindTheSpec Schema Migration v2.1 (Phase 2 Additions)
-- Target Engine: MySQL 8.4+
-- Non-destructive additions for requirements, interpretations, sessions, and divergences.

USE mind_the_spec;

-- 1. Requirements enhancements
ALTER TABLE requirements 
    ADD COLUMN IF NOT EXISTS priority VARCHAR(20) NOT NULL DEFAULT 'medium',
    ADD COLUMN IF NOT EXISTS acceptance_criteria TEXT NULL,
    ADD COLUMN IF NOT EXISTS created_by INT NULL;

-- 2. Interpretations enhancements
ALTER TABLE interpretations 
    ADD COLUMN IF NOT EXISTS edge_cases TEXT NULL,
    ADD COLUMN IF NOT EXISTS notes TEXT NULL;

-- 3. Sessions enhancements (support OPEN, LOCKED, REVEALED states)
ALTER TABLE interpretation_sessions 
    MODIFY COLUMN status VARCHAR(20) NOT NULL DEFAULT 'open';

-- 4. Divergences enhancements
ALTER TABLE divergences 
    ADD COLUMN IF NOT EXISTS category VARCHAR(50) NULL,
    ADD COLUMN IF NOT EXISTS severity VARCHAR(20) NOT NULL DEFAULT 'medium';
