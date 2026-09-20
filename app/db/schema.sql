PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS leads (
    id TEXT PRIMARY KEY,
    full_name TEXT NOT NULL,
    email TEXT NOT NULL,
    phone TEXT,
    service_requested TEXT NOT NULL,
    message TEXT NOT NULL,
    city TEXT,
    created_at TEXT NOT NULL,
    classification TEXT CHECK (
        classification IS NULL OR classification IN (
            'emergency_repair',
            'standard_repair',
            'installation',
            'maintenance',
            'quote_request',
            'irrelevant'
        )
    ),
    urgency TEXT CHECK (
        urgency IS NULL OR urgency IN ('critical', 'high', 'normal', 'low')
    ),
    status TEXT NOT NULL DEFAULT 'new' CHECK (
        status IN ('new', 'processing', 'open', 'review', 'closed', 'duplicate', 'failed')
    ),
    source TEXT NOT NULL DEFAULT 'website',
    ai_summary TEXT,
    follow_up_at TEXT,
    dedup_key TEXT UNIQUE,
    updated_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_leads_created_at ON leads(created_at);
CREATE INDEX IF NOT EXISTS idx_leads_status ON leads(status);
CREATE INDEX IF NOT EXISTS idx_leads_urgency ON leads(urgency);
CREATE INDEX IF NOT EXISTS idx_leads_follow_up_at ON leads(follow_up_at);

CREATE TABLE IF NOT EXISTS execution_logs (
    id TEXT PRIMARY KEY,
    lead_id TEXT,
    workflow_name TEXT NOT NULL,
    started_at TEXT NOT NULL,
    finished_at TEXT,
    outcome TEXT NOT NULL CHECK (
        outcome IN ('started', 'success', 'failed', 'manual_review', 'duplicate')
    ),
    error_type TEXT,
    error_message TEXT,
    metadata_json TEXT,
    FOREIGN KEY (lead_id) REFERENCES leads(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_execution_logs_lead_id ON execution_logs(lead_id);
CREATE INDEX IF NOT EXISTS idx_execution_logs_started_at ON execution_logs(started_at);
