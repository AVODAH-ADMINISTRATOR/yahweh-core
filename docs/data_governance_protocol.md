# Data Governance & Copyright Clearance Protocol
Status: ACTIVATED (Step 4)

## 1. Data Ingestion Triage
All incoming datasets must be categorized by their copyright status before entering the ingestion pipeline.

- **Category A: Public Domain / Open Source**
  - *Includes*: Masoretic Text (BHS), Nestle-Aland (where applicable via open license), Public Domain translations (e.g., KJV, ASV, Darby).
  - *Clearance*: Immediate integration authorized.
- **Category B: License-Required (Proprietary)**
  - *Includes*: Modern copyrighted translations (e.g., NIV, ESV, NASB).
  - *Clearance*: Requires signed MOU/Licensing Agreement. Data must be housed in encrypted, read-only volumes with strictly scoped API access.
- **Category C: Restricted/Research Only**
  - *Includes*: Fragmentary academic transcriptions (e.g., specific Qumran scroll editions with ongoing research rights).
  - *Clearance*: Restricted to specific internal researcher roles only.

## 2. The "Clean Room" Processing Pipeline
To maintain data purity, all ingested data—regardless of origin—must undergo the "Clean Room" protocol:
- **Sanitization**: Stripping of proprietary metadata or embedded DRM/watermarks.
- **Normalization**: Converting all inputs into the canonical project format (USFM/UTF-8).
- **Attribution Logging**: Every dataset, even if public domain, must be tagged with a unique source identifier to ensure accurate citations in the final engine output.

## 3. Attribution & Licensing Compliance
- **Machine Learning Attribution**: If copyrighted texts are used for model fine-tuning (e.g., style alignment), they must be marked as `training_data` and excluded from verbatim output generation to prevent copyright infringement.
- **Open Source Contribution**: The engine will adhere to the "Principle of Reciprocity"—any metadata generated that is derivative of open-source datasets shall be released back to the scholarly community under a Creative Commons Attribution-ShareAlike (CC BY-SA) license.

## 4. Governance Audit
- Quarterly reviews of ingested datasets.
- Immediate removal/quarantine of any dataset found to be non-compliant with copyright laws.
