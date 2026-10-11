PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS api_keys (
    id TEXT PRIMARY KEY,
    key_hash TEXT NOT NULL UNIQUE,
    owner_name TEXT NOT NULL,
    rate_limit_per_minute INTEGER NOT NULL DEFAULT 60,
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL DEFAULT (datetime('now', 'utc')),
    revoked_at TEXT
);

CREATE TABLE IF NOT EXISTS documents (
    id TEXT PRIMARY KEY,
    api_key_id TEXT,
    session_id TEXT,
    title TEXT NOT NULL,
    raw_text TEXT NOT NULL,
    character_count INTEGER NOT NULL,
    word_count INTEGER NOT NULL,
    sentence_count INTEGER NOT NULL,
    paragraph_count INTEGER NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now', 'utc')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now', 'utc')),
    FOREIGN KEY (api_key_id) REFERENCES api_keys(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS sentiment_evaluations (
    id TEXT PRIMARY KEY,
    document_id TEXT NOT NULL UNIQUE,
    polarity REAL NOT NULL,
    subjectivity REAL NOT NULL,
    classification TEXT NOT NULL CHECK (classification IN ('strongly_negative', 'negative', 'neutral', 'positive', 'strongly_positive')),
    positivity_score REAL NOT NULL,
    negativity_score REAL NOT NULL,
    neutrality_score REAL NOT NULL,
    compound_score REAL NOT NULL,
    joy_score REAL NOT NULL,
    sadness_score REAL NOT NULL,
    anger_score REAL NOT NULL,
    fear_score REAL NOT NULL,
    trust_score REAL NOT NULL,
    surprise_score REAL NOT NULL,
    disgust_score REAL NOT NULL,
    anticipation_score REAL NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now', 'utc')),
    FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS readability_evaluations (
    id TEXT PRIMARY KEY,
    document_id TEXT NOT NULL UNIQUE,
    flesch_reading_ease REAL NOT NULL,
    flesch_kincaid_grade REAL NOT NULL,
    gunning_fog_index REAL NOT NULL,
    coleman_liau_index REAL NOT NULL,
    smog_index REAL NOT NULL,
    automated_readability_index REAL NOT NULL,
    reading_time_seconds INTEGER NOT NULL,
    speaking_time_seconds INTEGER NOT NULL,
    syllable_count INTEGER NOT NULL,
    complex_word_count INTEGER NOT NULL,
    grade_level_consensus TEXT NOT NULL,
    cefr_equivalent TEXT NOT NULL CHECK (cefr_equivalent IN ('A1', 'A2', 'B1', 'B2', 'C1', 'C2')),
    created_at TEXT NOT NULL DEFAULT (datetime('now', 'utc')),
    FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_api_keys_key_hash ON api_keys(key_hash);
CREATE INDEX IF NOT EXISTS idx_documents_created_at ON documents(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_documents_api_key_id ON documents(api_key_id);
CREATE INDEX IF NOT EXISTS idx_documents_session_id ON documents(session_id);
CREATE INDEX IF NOT EXISTS idx_sentiment_evaluations_document_id ON sentiment_evaluations(document_id);
CREATE INDEX IF NOT EXISTS idx_sentiment_classification ON sentiment_evaluations(classification);
CREATE INDEX IF NOT EXISTS idx_readability_evaluations_document_id ON readability_evaluations(document_id);
CREATE INDEX IF NOT EXISTS idx_readability_cefr ON readability_evaluations(cefr_equivalent);
