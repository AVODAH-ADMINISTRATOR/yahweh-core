-- Initial Schema for Biblical Core Data

CREATE TABLE manuscripts (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    language VARCHAR(50) NOT NULL,
    date_century INT
);

CREATE TABLE canonical_texts (
    id SERIAL PRIMARY KEY,
    book VARCHAR(50) NOT NULL,
    chapter INT NOT NULL,
    verse INT NOT NULL,
    original_text TEXT NOT NULL,
    language VARCHAR(50) NOT NULL,
    manuscript_id INT REFERENCES manuscripts(id)
);

CREATE TABLE translations (
    id SERIAL PRIMARY KEY,
    text_id INT REFERENCES canonical_texts(id),
    target_language VARCHAR(50) NOT NULL,
    translated_text TEXT NOT NULL,
    model_version VARCHAR(50) NOT NULL,
    theological_flag BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE apparatus_criticus (
    id SERIAL PRIMARY KEY,
    text_id INT REFERENCES canonical_texts(id),
    variant_reading TEXT NOT NULL,
    manuscript_evidence JSONB,
    confidence_score FLOAT
);
