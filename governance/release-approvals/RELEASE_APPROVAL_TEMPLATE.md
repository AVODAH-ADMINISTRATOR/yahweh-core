# Release Approval Gate
Workload:
Environment: dev/staging/prod
Checklist:
- [ ] secrets scanning passed
- [ ] image scanning passed
- [ ] sbom generated evidence/sboms/
- [ ] benchmark-results evidence/benchmark-results/
- [ ] test-reports evidence/test-reports/
- [ ] security-scans evidence/security-scans/
- [ ] provenance evidence/provenance/
- [ ] checksums evidence/checksums/
- [ ] risk-register reviewed governance/risk-register.md
- [ ] rollback procedure documented
- [ ] RPO/RTO demonstrated
Approver:
Timestamp:
