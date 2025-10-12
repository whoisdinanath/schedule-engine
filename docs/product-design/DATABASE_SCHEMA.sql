-- ============================================================================
-- Academic Timetabling System - Database Schema
-- PostgreSQL 15+
-- Version: 1.0
-- ============================================================================

-- Enable UUID extension for unique identifiers (optional)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================================
-- ORGANIZATIONS & USERS
-- ============================================================================

-- Organizations table (Multi-tenancy support)
CREATE TABLE organizations (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    domain VARCHAR(100) UNIQUE,
    subscription_tier VARCHAR(50) DEFAULT 'basic', -- basic, professional, enterprise
    max_courses INTEGER DEFAULT 50,
    max_instructors INTEGER DEFAULT 20,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Users table
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    organization_id INTEGER REFERENCES organizations(id) ON DELETE CASCADE,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL CHECK (role IN ('admin', 'scheduler', 'instructor', 'viewer')),
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    is_active BOOLEAN DEFAULT true,
    email_verified BOOLEAN DEFAULT false,
    last_login TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Password reset tokens
CREATE TABLE password_reset_tokens (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    token VARCHAR(255) UNIQUE NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    used BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- ACADEMIC STRUCTURE
-- ============================================================================

-- Departments
CREATE TABLE departments (
    id SERIAL PRIMARY KEY,
    organization_id INTEGER REFERENCES organizations(id) ON DELETE CASCADE,
    code VARCHAR(20) NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(organization_id, code)
);

-- Courses
CREATE TABLE courses (
    id SERIAL PRIMARY KEY,
    organization_id INTEGER REFERENCES organizations(id) ON DELETE CASCADE,
    department_id INTEGER REFERENCES departments(id) ON DELETE SET NULL,
    course_code VARCHAR(50) NOT NULL,
    course_title VARCHAR(255) NOT NULL,
    credits INTEGER NOT NULL CHECK (credits > 0),
    lecture_hours INTEGER DEFAULT 0 CHECK (lecture_hours >= 0),
    tutorial_hours INTEGER DEFAULT 0 CHECK (tutorial_hours >= 0),
    practical_hours INTEGER DEFAULT 0 CHECK (practical_hours >= 0),
    semester INTEGER CHECK (semester >= 1 AND semester <= 8),
    required_room_features JSONB DEFAULT '[]'::jsonb,
    description TEXT,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(organization_id, course_code)
);

-- Instructors
CREATE TABLE instructors (
    id SERIAL PRIMARY KEY,
    organization_id INTEGER REFERENCES organizations(id) ON DELETE CASCADE,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    instructor_code VARCHAR(50) NOT NULL,
    name VARCHAR(255) NOT NULL,
    department_id INTEGER REFERENCES departments(id) ON DELETE SET NULL,
    email VARCHAR(255),
    phone VARCHAR(50),
    max_weekly_hours INTEGER DEFAULT 40 CHECK (max_weekly_hours > 0),
    availability JSONB DEFAULT '{}'::jsonb,
    preferences JSONB DEFAULT '{}'::jsonb,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(organization_id, instructor_code)
);

-- Rooms
CREATE TABLE rooms (
    id SERIAL PRIMARY KEY,
    organization_id INTEGER REFERENCES organizations(id) ON DELETE CASCADE,
    room_code VARCHAR(50) NOT NULL,
    room_name VARCHAR(255),
    building VARCHAR(100),
    floor INTEGER,
    capacity INTEGER NOT NULL CHECK (capacity > 0),
    room_type VARCHAR(50) CHECK (room_type IN ('lecture', 'lab', 'tutorial', 'seminar', 'workshop')),
    features JSONB DEFAULT '[]'::jsonb,
    availability JSONB DEFAULT '{}'::jsonb,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(organization_id, room_code)
);

-- Student Groups
CREATE TABLE student_groups (
    id SERIAL PRIMARY KEY,
    organization_id INTEGER REFERENCES organizations(id) ON DELETE CASCADE,
    group_code VARCHAR(50) NOT NULL,
    group_name VARCHAR(255),
    program VARCHAR(100),
    semester INTEGER CHECK (semester >= 1 AND semester <= 8),
    year INTEGER,
    student_count INTEGER DEFAULT 0 CHECK (student_count >= 0),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(organization_id, group_code)
);

-- ============================================================================
-- RELATIONSHIPS
-- ============================================================================

-- Course-Instructor assignments
CREATE TABLE course_instructors (
    id SERIAL PRIMARY KEY,
    course_id INTEGER REFERENCES courses(id) ON DELETE CASCADE,
    instructor_id INTEGER REFERENCES instructors(id) ON DELETE CASCADE,
    is_primary BOOLEAN DEFAULT false,
    session_type VARCHAR(20) CHECK (session_type IN ('lecture', 'tutorial', 'practical', 'all')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(course_id, instructor_id, session_type)
);

-- Group course enrollments
CREATE TABLE group_enrollments (
    id SERIAL PRIMARY KEY,
    group_id INTEGER REFERENCES student_groups(id) ON DELETE CASCADE,
    course_id INTEGER REFERENCES courses(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(group_id, course_id)
);

-- ============================================================================
-- SCHEDULING
-- ============================================================================

-- Schedule runs (optimization runs)
CREATE TABLE schedule_runs (
    id SERIAL PRIMARY KEY,
    organization_id INTEGER REFERENCES organizations(id) ON DELETE CASCADE,
    created_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
    name VARCHAR(255),
    academic_year VARCHAR(20),
    semester INTEGER,
    status VARCHAR(50) DEFAULT 'pending' CHECK (status IN ('pending', 'queued', 'running', 'completed', 'failed', 'cancelled')),
    algorithm_config JSONB DEFAULT '{}'::jsonb,
    fitness_score DECIMAL(10, 6),
    hard_violations INTEGER DEFAULT 0,
    soft_violations INTEGER DEFAULT 0,
    runtime_seconds INTEGER,
    progress_percentage INTEGER DEFAULT 0 CHECK (progress_percentage >= 0 AND progress_percentage <= 100),
    error_message TEXT,
    is_published BOOLEAN DEFAULT false,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Scheduled sessions (individual time slots)
CREATE TABLE scheduled_sessions (
    id SERIAL PRIMARY KEY,
    schedule_run_id INTEGER REFERENCES schedule_runs(id) ON DELETE CASCADE,
    course_id INTEGER REFERENCES courses(id) ON DELETE CASCADE,
    instructor_id INTEGER REFERENCES instructors(id) ON DELETE CASCADE,
    room_id INTEGER REFERENCES rooms(id) ON DELETE CASCADE,
    group_id INTEGER REFERENCES student_groups(id) ON DELETE CASCADE,
    day_of_week VARCHAR(20) NOT NULL CHECK (day_of_week IN ('monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday')),
    time_slot VARCHAR(50) NOT NULL,
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    session_type VARCHAR(20) CHECK (session_type IN ('lecture', 'tutorial', 'practical')),
    duration_minutes INTEGER NOT NULL CHECK (duration_minutes > 0),
    is_manually_edited BOOLEAN DEFAULT false,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- CONSTRAINTS CONFIGURATION
-- ============================================================================

-- Constraint configurations
CREATE TABLE constraint_configs (
    id SERIAL PRIMARY KEY,
    organization_id INTEGER REFERENCES organizations(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    constraint_type VARCHAR(50) CHECK (constraint_type IN ('hard', 'soft')),
    constraint_category VARCHAR(100), -- instructor, room, group, time, etc.
    weight DECIMAL(5, 2) DEFAULT 1.0 CHECK (weight >= 0),
    is_active BOOLEAN DEFAULT true,
    parameters JSONB DEFAULT '{}'::jsonb,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(organization_id, name)
);

-- ============================================================================
-- AUDIT & LOGGING
-- ============================================================================

-- Audit logs
CREATE TABLE audit_logs (
    id SERIAL PRIMARY KEY,
    organization_id INTEGER REFERENCES organizations(id) ON DELETE CASCADE,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    action VARCHAR(100) NOT NULL,
    entity_type VARCHAR(50),
    entity_id INTEGER,
    changes JSONB DEFAULT '{}'::jsonb,
    ip_address VARCHAR(50),
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- System logs
CREATE TABLE system_logs (
    id SERIAL PRIMARY KEY,
    level VARCHAR(20) CHECK (level IN ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL')),
    module VARCHAR(100),
    message TEXT NOT NULL,
    details JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- NOTIFICATIONS
-- ============================================================================

-- Notifications
CREATE TABLE notifications (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    type VARCHAR(50) NOT NULL,
    title VARCHAR(255) NOT NULL,
    message TEXT,
    data JSONB DEFAULT '{}'::jsonb,
    is_read BOOLEAN DEFAULT false,
    read_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- INDEXES FOR PERFORMANCE
-- ============================================================================

-- Organizations indexes
CREATE INDEX idx_organizations_domain ON organizations(domain) WHERE domain IS NOT NULL;

-- Users indexes
CREATE INDEX idx_users_org ON users(organization_id);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_role ON users(role);

-- Courses indexes
CREATE INDEX idx_courses_org ON courses(organization_id);
CREATE INDEX idx_courses_dept ON courses(department_id);
CREATE INDEX idx_courses_code ON courses(course_code);
CREATE INDEX idx_courses_active ON courses(is_active);

-- Instructors indexes
CREATE INDEX idx_instructors_org ON instructors(organization_id);
CREATE INDEX idx_instructors_dept ON instructors(department_id);
CREATE INDEX idx_instructors_active ON instructors(is_active);

-- Rooms indexes
CREATE INDEX idx_rooms_org ON rooms(organization_id);
CREATE INDEX idx_rooms_type ON rooms(room_type);
CREATE INDEX idx_rooms_active ON rooms(is_active);

-- Student groups indexes
CREATE INDEX idx_groups_org ON student_groups(organization_id);
CREATE INDEX idx_groups_program ON student_groups(program);
CREATE INDEX idx_groups_active ON student_groups(is_active);

-- Schedule runs indexes
CREATE INDEX idx_schedule_runs_org ON schedule_runs(organization_id);
CREATE INDEX idx_schedule_runs_status ON schedule_runs(status);
CREATE INDEX idx_schedule_runs_org_status ON schedule_runs(organization_id, status);
CREATE INDEX idx_schedule_runs_created ON schedule_runs(created_at DESC);

-- Scheduled sessions indexes
CREATE INDEX idx_scheduled_sessions_run ON scheduled_sessions(schedule_run_id);
CREATE INDEX idx_scheduled_sessions_course ON scheduled_sessions(course_id);
CREATE INDEX idx_scheduled_sessions_instructor ON scheduled_sessions(instructor_id);
CREATE INDEX idx_scheduled_sessions_room ON scheduled_sessions(room_id);
CREATE INDEX idx_scheduled_sessions_group ON scheduled_sessions(group_id);
CREATE INDEX idx_scheduled_sessions_day_time ON scheduled_sessions(day_of_week, time_slot);

-- Audit logs indexes
CREATE INDEX idx_audit_logs_org ON audit_logs(organization_id);
CREATE INDEX idx_audit_logs_user ON audit_logs(user_id);
CREATE INDEX idx_audit_logs_created ON audit_logs(created_at DESC);

-- Notifications indexes
CREATE INDEX idx_notifications_user ON notifications(user_id);
CREATE INDEX idx_notifications_unread ON notifications(user_id, is_read) WHERE is_read = false;

-- ============================================================================
-- TRIGGERS FOR UPDATED_AT TIMESTAMP
-- ============================================================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply trigger to tables with updated_at column
CREATE TRIGGER update_organizations_updated_at BEFORE UPDATE ON organizations
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_departments_updated_at BEFORE UPDATE ON departments
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_courses_updated_at BEFORE UPDATE ON courses
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_instructors_updated_at BEFORE UPDATE ON instructors
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_rooms_updated_at BEFORE UPDATE ON rooms
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_student_groups_updated_at BEFORE UPDATE ON student_groups
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_schedule_runs_updated_at BEFORE UPDATE ON schedule_runs
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_scheduled_sessions_updated_at BEFORE UPDATE ON scheduled_sessions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_constraint_configs_updated_at BEFORE UPDATE ON constraint_configs
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- SAMPLE DATA (Optional - for development/testing)
-- ============================================================================

-- Insert sample organization
INSERT INTO organizations (name, domain, subscription_tier) VALUES 
('Demo University', 'demo.edu', 'professional');

-- Note: Add more sample data as needed for development
