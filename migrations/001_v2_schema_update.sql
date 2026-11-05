-- MindTheSpec Schema Migration v2
-- Target Engine: MySQL 8.4+
-- Non-destructive: upgrades existing empty schema to full PRD v2 specification.

USE mind_the_spec;

-- Disable FK checks during schema alignment
SET FOREIGN_KEY_CHECKS = 0;

-- 1. Ensure projects table has status & updated_at
CREATE TABLE IF NOT EXISTS projects (
    project_id INT AUTO_INCREMENT PRIMARY KEY,
    project_name VARCHAR(150) NOT NULL,
    description TEXT,
    owner_id INT NOT NULL,
    status ENUM('active', 'archived') NOT NULL DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    KEY idx_project_owner (owner_id),
    CONSTRAINT fk_project_owner FOREIGN KEY (owner_id) REFERENCES users (user_id) ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 2. Project Members table (FR-01, FR-11)
CREATE TABLE IF NOT EXISTS project_members (
    project_id INT NOT NULL,
    user_id INT NOT NULL,
    role ENUM('owner', 'analyst', 'developer', 'tester', 'observer') NOT NULL DEFAULT 'developer',
    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (project_id, user_id),
    CONSTRAINT fk_member_project FOREIGN KEY (project_id) REFERENCES projects (project_id) ON DELETE CASCADE,
    CONSTRAINT fk_member_user FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 3. Ensure requirements table has req_code, status enum, current_version_id
CREATE TABLE IF NOT EXISTS requirements (
    requirement_id INT AUTO_INCREMENT PRIMARY KEY,
    project_id INT NOT NULL,
    req_code VARCHAR(50) NOT NULL DEFAULT 'REQ-001',
    title VARCHAR(200) NOT NULL,
    description TEXT NOT NULL,
    status ENUM('draft', 'active', 'resolved', 'archived') NOT NULL DEFAULT 'draft',
    version INT NOT NULL DEFAULT 1,
    current_version_id INT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    KEY idx_req_project (project_id),
    UNIQUE KEY uq_project_req_code (project_id, req_code),
    CONSTRAINT fk_requirement_project FOREIGN KEY (project_id) REFERENCES projects (project_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 4. Requirement Versions table (FR-03, FR-10)
CREATE TABLE IF NOT EXISTS requirement_versions (
    version_id INT AUTO_INCREMENT PRIMARY KEY,
    requirement_id INT NOT NULL,
    version_no INT NOT NULL DEFAULT 1,
    body TEXT NOT NULL,
    acceptance_notes TEXT NULL,
    created_by INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uq_req_version_no (requirement_id, version_no),
    KEY idx_version_req (requirement_id),
    CONSTRAINT fk_version_requirement FOREIGN KEY (requirement_id) REFERENCES requirements (requirement_id) ON DELETE CASCADE,
    CONSTRAINT fk_version_user FOREIGN KEY (created_by) REFERENCES users (user_id) ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 5. Interpretation Sessions table (FR-04, FR-05)
CREATE TABLE IF NOT EXISTS interpretation_sessions (
    session_id INT AUTO_INCREMENT PRIMARY KEY,
    requirement_version_id INT NOT NULL,
    created_by INT NOT NULL,
    status ENUM('draft', 'collecting', 'locked', 'analyzed', 'resolved') NOT NULL DEFAULT 'draft',
    mode ENUM('standard', 'self_comparison') NOT NULL DEFAULT 'standard',
    locked_at TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    KEY idx_session_version (requirement_version_id),
    KEY idx_session_status (status),
    CONSTRAINT fk_session_version FOREIGN KEY (requirement_version_id) REFERENCES requirement_versions (version_id) ON DELETE RESTRICT,
    CONSTRAINT fk_session_user FOREIGN KEY (created_by) REFERENCES users (user_id) ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 6. Interpretations table with structured typed fields (FR-04, Section 6)
CREATE TABLE IF NOT EXISTS interpretations (
    interpretation_id INT AUTO_INCREMENT PRIMARY KEY,
    session_id INT NOT NULL,
    requirement_id INT NOT NULL,
    user_id INT NOT NULL,
    perspective VARCHAR(100) NOT NULL,
    actor VARCHAR(100) NULL,
    expected_behavior TEXT NOT NULL,
    trigger_conditions TEXT NULL,
    delivery_hours INT NULL,
    constraints TEXT NULL,
    acceptance_criteria TEXT NULL,
    interpretation_text TEXT NULL,
    assumptions TEXT NULL,
    submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    KEY idx_interp_session (session_id),
    KEY idx_interp_user (user_id),
    UNIQUE KEY uq_session_user_perspective (session_id, user_id, perspective),
    CONSTRAINT fk_interp_session FOREIGN KEY (session_id) REFERENCES interpretation_sessions (session_id) ON DELETE CASCADE,
    CONSTRAINT fk_interp_requirement FOREIGN KEY (requirement_id) REFERENCES requirements (requirement_id) ON DELETE CASCADE,
    CONSTRAINT fk_interp_user FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 7. Divergences table (FR-05)
CREATE TABLE IF NOT EXISTS divergences (
    divergence_id INT AUTO_INCREMENT PRIMARY KEY,
    session_id INT NOT NULL,
    field_name VARCHAR(100) NOT NULL,
    kind VARCHAR(50) NOT NULL DEFAULT 'structured_mismatch',
    evidence_json JSON NOT NULL,
    review_status ENUM('open', 'resolved', 'ignored') NOT NULL DEFAULT 'open',
    fingerprint VARCHAR(64) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    KEY idx_divergence_session (session_id),
    UNIQUE KEY uq_session_fingerprint (session_id, fingerprint),
    CONSTRAINT fk_divergence_session FOREIGN KEY (session_id) REFERENCES interpretation_sessions (session_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 8. Divergence-Interpretations association (FR-05, Section 7)
CREATE TABLE IF NOT EXISTS divergence_interpretations (
    divergence_id INT NOT NULL,
    interpretation_id INT NOT NULL,
    PRIMARY KEY (divergence_id, interpretation_id),
    CONSTRAINT fk_di_divergence FOREIGN KEY (divergence_id) REFERENCES divergences (divergence_id) ON DELETE CASCADE,
    CONSTRAINT fk_di_interpretation FOREIGN KEY (interpretation_id) REFERENCES interpretations (interpretation_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 9. Resolutions table (FR-06)
CREATE TABLE IF NOT EXISTS resolutions (
    resolution_id INT AUTO_INCREMENT PRIMARY KEY,
    session_id INT NOT NULL,
    statement TEXT NOT NULL,
    rationale TEXT NOT NULL,
    decided_by INT NOT NULL,
    decided_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uq_session_resolution (session_id),
    KEY idx_resolution_decided_by (decided_by),
    CONSTRAINT fk_resolution_session FOREIGN KEY (session_id) REFERENCES interpretation_sessions (session_id) ON DELETE CASCADE,
    CONSTRAINT fk_resolution_user FOREIGN KEY (decided_by) REFERENCES users (user_id) ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 10. Audit Logs table (FR-07)
CREATE TABLE IF NOT EXISTS audit_logs (
    log_id INT AUTO_INCREMENT PRIMARY KEY,
    project_id INT NOT NULL,
    user_id INT NULL,
    action VARCHAR(100) NOT NULL,
    entity_type VARCHAR(50) NOT NULL,
    entity_id INT NOT NULL,
    details TEXT NULL,
    metadata_json JSON NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    KEY idx_audit_project_time (project_id, created_at),
    KEY idx_audit_user (user_id),
    CONSTRAINT fk_audit_project FOREIGN KEY (project_id) REFERENCES projects (project_id) ON DELETE CASCADE,
    CONSTRAINT fk_audit_user FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Re-enable FK checks
SET FOREIGN_KEY_CHECKS = 1;
