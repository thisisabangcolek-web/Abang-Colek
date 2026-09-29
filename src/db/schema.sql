-- ==============================================================================
-- ABANGCOLEK Forensic Evidence & Knowledge Graph Enterprise Schema for Supabase
-- Target: PostgreSQL 15+ / Supabase
-- Specification: Evidence-First Provenance, Neutral JEV Classification & Graph
-- ==============================================================================

-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ------------------------------------------------------------------------------
-- 1. EVIDENCE REGISTRY & NORMALIZED CAPTURES
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.evidence_records (
    capture_id TEXT PRIMARY KEY,
    content_id TEXT NOT NULL,
    normalized_id TEXT,
    platform TEXT NOT NULL,
    native_id TEXT,
    raw_hash TEXT NOT NULL UNIQUE,
    source_url TEXT,
    record_kind TEXT NOT NULL,
    collector TEXT,
    authoritative BOOLEAN NOT NULL DEFAULT true,
    synthetic BOOLEAN NOT NULL DEFAULT false,
    capture_verified BOOLEAN NOT NULL DEFAULT true,
    published_at TIMESTAMPTZ,
    captured_at TIMESTAMPTZ,
    text_content TEXT,
    raw_payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now())
);

COMMENT ON TABLE public.evidence_records IS 'Immutable registry of verified forensic evidence captures and normalized social media posts.';

-- ------------------------------------------------------------------------------
-- 2. JEV SYSTEM-1 DECISIONS & EPISTEMIC CLAIMS
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.jev_decisions (
    decision_id TEXT PRIMARY KEY,
    capture_id TEXT NOT NULL REFERENCES public.evidence_records(capture_id) ON DELETE CASCADE,
    content_id TEXT NOT NULL,
    normalized_id TEXT,
    evaluation_type TEXT NOT NULL, -- content, signal, interaction, complaint
    model_requested TEXT,
    model_resolved TEXT,
    confidence REAL,
    classified JSONB NOT NULL DEFAULT '{}'::jsonb,
    answers JSONB NOT NULL DEFAULT '{}'::jsonb,
    authoritative BOOLEAN NOT NULL DEFAULT true,
    decision_engine TEXT NOT NULL DEFAULT 'TYPESAFE_JEV',
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now())
);

COMMENT ON TABLE public.jev_decisions IS 'Machine-classified epistemic claims produced by TypeSafe JEV System-1 with deterministic cache keys.';

-- ------------------------------------------------------------------------------
-- 3. KNOWLEDGE GRAPH: ENTITIES
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.knowledge_entities (
    entity_id TEXT PRIMARY KEY,
    entity_type TEXT NOT NULL, -- EVIDENCE, PLATFORM, BRAND, PERSON, LOCATION, PRODUCT
    name TEXT NOT NULL,
    canonical_name TEXT,
    trust_score REAL,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now())
);

COMMENT ON TABLE public.knowledge_entities IS 'Observed entities within the ABANGCOLEK operational footprint without unverified cross-merging.';

-- ------------------------------------------------------------------------------
-- 4. KNOWLEDGE GRAPH: RELATIONSHIPS
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.knowledge_relationships (
    rel_id TEXT PRIMARY KEY,
    source_id TEXT NOT NULL REFERENCES public.knowledge_entities(entity_id) ON DELETE CASCADE,
    target_id TEXT NOT NULL REFERENCES public.knowledge_entities(entity_id) ON DELETE CASCADE,
    relation_type TEXT NOT NULL,
    confidence REAL,
    epistemology_class TEXT NOT NULL DEFAULT 'OBSERVED_FACT', -- OBSERVED_FACT, CLASSIFICATION, INFERENCE
    first_seen TIMESTAMPTZ,
    last_seen TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now())
);

COMMENT ON TABLE public.knowledge_relationships IS 'Grounded relationships connecting entities, enforced by evidence citations.';

CREATE TABLE IF NOT EXISTS public.knowledge_relationship_evidence (
    rel_id TEXT NOT NULL REFERENCES public.knowledge_relationships(rel_id) ON DELETE CASCADE,
    capture_id TEXT NOT NULL REFERENCES public.evidence_records(capture_id) ON DELETE CASCADE,
    PRIMARY KEY (rel_id, capture_id)
);

-- ------------------------------------------------------------------------------
-- 5. EPISTEMOLOGY LEDGER (Facts, Inferences, Hypotheses)
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.knowledge_epistemology (
    item_id TEXT PRIMARY KEY,
    item_type TEXT NOT NULL, -- CLASSIFICATION, INFERENCE, HYPOTHESIS, OBSERVED_FACT
    statement TEXT NOT NULL,
    confidence REAL,
    status TEXT NOT NULL DEFAULT 'SUPPORTED', -- SUPPORTED, REJECTED, UNVERIFIED
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now())
);

CREATE TABLE IF NOT EXISTS public.knowledge_epistemology_evidence (
    item_id TEXT NOT NULL REFERENCES public.knowledge_epistemology(item_id) ON DELETE CASCADE,
    capture_id TEXT NOT NULL REFERENCES public.evidence_records(capture_id) ON DELETE CASCADE,
    PRIMARY KEY (item_id, capture_id)
);

-- ------------------------------------------------------------------------------
-- 6. CHRONOLOGICAL TIMELINE EVENTS
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.knowledge_timeline_events (
    event_id TEXT PRIMARY KEY,
    event_date TIMESTAMPTZ,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    entity_ids JSONB NOT NULL DEFAULT '[]'::jsonb,
    confidence REAL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now())
);

CREATE TABLE IF NOT EXISTS public.knowledge_timeline_evidence (
    event_id TEXT NOT NULL REFERENCES public.knowledge_timeline_events(event_id) ON DELETE CASCADE,
    capture_id TEXT NOT NULL REFERENCES public.evidence_records(capture_id) ON DELETE CASCADE,
    PRIMARY KEY (event_id, capture_id)
);

-- ------------------------------------------------------------------------------
-- 7. PROCESSING RUNS & BI METRICS SNAPSHOTS
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.processing_runs (
    run_id TEXT PRIMARY KEY,
    input_fingerprint TEXT,
    total_posts INT DEFAULT 0,
    total_normalized_records INT DEFAULT 0,
    total_jev_decisions INT DEFAULT 0,
    counts JSONB NOT NULL DEFAULT '{}'::jsonb,
    status TEXT NOT NULL DEFAULT 'ACTIVE',
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now())
);

-- ------------------------------------------------------------------------------
-- 8. BUSINESS VALIDATION & OWNER INTERVIEW BOARD
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.business_questions (
    question_id TEXT PRIMARY KEY,
    question TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'INTERNAL_VALIDATION_REQUIRED',
    missing_evidence TEXT,
    owner_answer TEXT,
    workflow_steps JSONB NOT NULL DEFAULT '[]'::jsonb,
    validated_by TEXT,
    validated_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now())
);

-- ------------------------------------------------------------------------------
-- 9. HUMAN CLAIM AUDIT & REVIEWS
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.claim_reviews (
    review_id TEXT PRIMARY KEY,
    decision_id TEXT NOT NULL REFERENCES public.jev_decisions(decision_id) ON DELETE CASCADE,
    reviewer TEXT NOT NULL,
    status TEXT NOT NULL, -- APPROVED, REJECTED, NEEDS_INTERVIEW
    notes TEXT,
    reviewed_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now())
);

-- ------------------------------------------------------------------------------
-- INDEXES (Optimized for Query Performance & Foreign Key Constraints)
-- ------------------------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_evidence_platform ON public.evidence_records(platform);
CREATE INDEX IF NOT EXISTS idx_evidence_record_kind ON public.evidence_records(record_kind);
CREATE INDEX IF NOT EXISTS idx_evidence_raw_hash ON public.evidence_records(raw_hash);
CREATE INDEX IF NOT EXISTS idx_evidence_raw_payload_gin ON public.evidence_records USING gin (raw_payload);

CREATE INDEX IF NOT EXISTS idx_decisions_capture_id ON public.jev_decisions(capture_id);
CREATE INDEX IF NOT EXISTS idx_decisions_eval_type ON public.jev_decisions(evaluation_type);
CREATE INDEX IF NOT EXISTS idx_decisions_classified_gin ON public.jev_decisions USING gin (classified);

CREATE INDEX IF NOT EXISTS idx_entities_type ON public.knowledge_entities(entity_type);
CREATE INDEX IF NOT EXISTS idx_entities_metadata_gin ON public.knowledge_entities USING gin (metadata);

CREATE INDEX IF NOT EXISTS idx_relationships_source ON public.knowledge_relationships(source_id);
CREATE INDEX IF NOT EXISTS idx_relationships_target ON public.knowledge_relationships(target_id);
CREATE INDEX IF NOT EXISTS idx_relationships_type ON public.knowledge_relationships(relation_type);

CREATE INDEX IF NOT EXISTS idx_epistemology_type ON public.knowledge_epistemology(item_type);
CREATE INDEX IF NOT EXISTS idx_timeline_date ON public.knowledge_timeline_events(event_date);

-- ------------------------------------------------------------------------------
-- ROW LEVEL SECURITY (RLS) POLICIES
-- ------------------------------------------------------------------------------
ALTER TABLE public.evidence_records ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.jev_decisions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.knowledge_entities ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.knowledge_relationships ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.knowledge_relationship_evidence ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.knowledge_epistemology ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.knowledge_epistemology_evidence ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.knowledge_timeline_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.knowledge_timeline_evidence ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.processing_runs ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.business_questions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.claim_reviews ENABLE ROW LEVEL SECURITY;

-- Read-only access for authenticated and anonymous users
DO $$
DECLARE
    tbl text;
BEGIN
    FOR tbl IN SELECT tablename FROM pg_tables WHERE schemaname = 'public' AND tablename IN (
        'evidence_records', 'jev_decisions', 'knowledge_entities', 'knowledge_relationships',
        'knowledge_relationship_evidence', 'knowledge_epistemology', 'knowledge_epistemology_evidence',
        'knowledge_timeline_events', 'knowledge_timeline_evidence', 'processing_runs',
        'business_questions', 'claim_reviews'
    )
    LOOP
        EXECUTE format('DROP POLICY IF EXISTS %I_select_policy ON public.%I', tbl, tbl);
        EXECUTE format('CREATE POLICY %I_select_policy ON public.%I FOR SELECT TO anon, authenticated USING (true)', tbl, tbl);
        
        EXECUTE format('DROP POLICY IF EXISTS %I_service_role_policy ON public.%I', tbl, tbl);
        EXECUTE format('CREATE POLICY %I_service_role_policy ON public.%I FOR ALL TO service_role USING (true) WITH CHECK (true)', tbl, tbl);
    END LOOP;
END $$;

-- ------------------------------------------------------------------------------
-- VIEWS (Security Invoker enabled for safe PostgreSQL 15+ querying)
-- ------------------------------------------------------------------------------
CREATE OR REPLACE VIEW public.v_evidence_decision_summary WITH (security_invoker = true) AS
SELECT 
    e.capture_id,
    e.platform,
    e.record_kind,
    e.source_url,
    e.published_at,
    SUBSTRING(e.text_content FROM 1 FOR 250) AS excerpt,
    COUNT(d.decision_id) AS total_decisions,
    MAX(CASE WHEN d.evaluation_type = 'content' THEN d.classified->>'brand' END) AS detected_brand,
    MAX(CASE WHEN d.evaluation_type = 'content' THEN d.classified->>'business_function' END) AS business_function,
    MAX(CASE WHEN d.evaluation_type = 'content' THEN d.classified->>'sales_channel' END) AS sales_channel
FROM public.evidence_records e
LEFT JOIN public.jev_decisions d ON e.capture_id = d.capture_id
GROUP BY e.capture_id, e.platform, e.record_kind, e.source_url, e.published_at, e.text_content;
