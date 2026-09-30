# Risk Register - NIST AI RMF Govern/Map/Measure/Manage
Date: 2026-09-30 TOTAL 118 SEALED
| risk_id | category | description | likelihood | impact | owner | mitigation | status |
|---|---|---|---|---|---|---|---|
| R-001 | security | secret leakage on push | medium | high | security | push protection + secrets scanning | open |
| R-002 | integrity | untrusted research auto-ingest | high | high | governance | review-gate + parameterized queries only | mitigated by protocol |
| R-003 | availability | GPU starvation | medium | medium | platform | quotas + priorities + autoscaling | open |
| R-004 | compliance | data lineage gap | medium | high | data steward | lineage + catalog + audit ledger | open |
