// Neo4j Schema Constraints for Variant Matrix

// Ensure unique constraints on Manuscripts
CREATE CONSTRAINT FOR (m:Manuscript) REQUIRE m.name IS UNIQUE;

// Ensure unique constraints on Textual Base Nodes
CREATE CONSTRAINT FOR (t:TextNode) REQUIRE t.verse_id IS UNIQUE;

// Example Data Model Concepts:
// (m:Manuscript)-[:CONTAINS]->(r:Reading)
// (r:Reading)-[:IS_VARIANT_OF]->(t:TextNode)
// (r:Reading)-[:SUPPORTS_THEOLOGY]->(th:TheologicalConcept)
