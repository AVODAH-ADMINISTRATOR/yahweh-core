# Technical Design Document: NLP Pipeline & Translation Architecture

## 1. System Overview
The translation engine utilizes a Cross-Attention Network Architecture to align ancient language tokens (Source) with modern language equivalents (Target). The system incorporates theological guardrails and a robust Textual Criticism Variant Matrix.

## 2. Tokenization & Normalization
- **Morphological Analysis:** Words are decomposed into roots, stems, prefixes, and suffixes (e.g., Binyanim in Hebrew).
- **Normalization:** Diacritics (niqqud, cantillation marks) and breathings are normalized to ensure consistent embedding representation.

## 3. Cross-Attention Network Architecture
The core model uses Transformer-based cross-attention. 
- **Encoder:** Processes the normalized source text alongside morphological tags.
- **Decoder:** Generates the target text.
- **Variant Matrix Injection:** During encoding, variant readings are injected as alternative attention pathways, allowing the model to weigh different textual traditions.

## 4. Theological Guardrail Logic
A secondary "critic" model evaluates the generated translation against a knowledge graph of theological tenets. 
- If a translation violates a hard constraint, it is flagged for manual review.
- If it passes, it proceeds to the automated quality assurance pipeline.

## 5. Microservices Architecture (Docker/K8s)
- **API Gateway:** Routes requests and handles authentication.
- **NLP Inference Service:** GPU-accelerated service running the Transformer models.
- **Variant DB Service:** Interface to Neo4j graph database for tracing textual history.
- **Core DB Service:** PostgreSQL for storing final translations and user data.
