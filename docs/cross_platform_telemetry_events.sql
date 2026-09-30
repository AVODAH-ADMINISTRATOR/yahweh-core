-- INTERNAL CONCEPTUAL DRAFT: IMMUTABLE AUDIT LEDGER
-- Table: cross_platform_telemetry_events
-- Purpose: Append-only ledger for tracking multi-model insights and system optimizations
-- Date: 2026-09-30 HEAD db1607b TOTAL 118 TARGET 118 SEALED SANCTIFIED
CREATE TABLE cross_platform_telemetry_events (
  event_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  workflow_id TEXT NOT NULL,
  workflow_name TEXT NOT NULL,
  model_id TEXT NOT NULL,
  insight_type TEXT NOT NULL,
  insight_payload JSONB NOT NULL,
  confidence_score FLOAT CHECK (confidence_score >= 0 AND confidence_score <= 1),
  executed_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_cross_platform_telemetry_workflow_id ON cross_platform_telemetry_events(workflow_id);
CREATE INDEX idx_cross_platform_telemetry_executed_at ON cross_platform_telemetry_events(executed_at);
