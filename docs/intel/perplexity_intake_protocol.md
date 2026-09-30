# Perplexity Intel Intake - Antiquity Complexity
Date: 2026-09-30 HEAD c97a7c0 TOTAL 118 SEALED
Purpose: Append-only intake for Perplexity research - antiquity aligned insight telemetry
Source: Perplexity AI
Target: council_os/intel.py + cross_platform_telemetry_events

Protocol:
1. Paste Perplexity output as JSON in audit/intel-perplexity/
2. Validate antiquity alignment - Ethiopian Orthodox corpus, biblical covenant
3. Ingest to cross_platform_telemetry_events with insight_type='perplexity_intel'
4. Confidence score 0-1 - PSQL verified
5. Append-only - No overwrite - 118 seal preservation

SQL insertion example:
INSERT INTO cross_platform_telemetry_events 
(workflow_id, workflow_name, model_id, insight_type, insight_payload, confidence_score)
VALUES 
('perplexity-intake-2026-09-30', 'antiquity-complexity', 'perplexity', 'perplexity_intel', '{"source":"perplexity","antiquity_score":0.95}'::jsonb, 0.95);
