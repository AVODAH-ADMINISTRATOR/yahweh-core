class Neo4jConnectorStub:
    def get_manuscript_metadata(self, siglum: str):
        # Stub to fetch manuscript dating, provenance, and text-type from Graph
        pass

class PostgresConnectorStub:
    def get_canonical_verse(self, bcv_ref: str):
        # Stub to fetch the accepted NA28/BHS base text
        pass
