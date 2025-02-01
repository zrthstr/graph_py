from neo4j import GraphDatabase
from typing import Dict, Any, Optional

class Neo4jDB:
    def __init__(self, *, 
                 uri: str,
                 user: str,
                 password: str):
        self.driver = GraphDatabase.driver(uri=uri, auth=(user, password))

    def execute(self, *, query: str, parameters: Optional[Dict[str, Any]] = None):
        with self.driver.session() as session:
            return session.run(query=query, parameters=parameters or {})

    def execute_many(self, *, query: str, params: Optional[Dict[str, Any]] = None) -> list:
        with self.driver.session() as session:
            return list(session.run(query=query, parameters=params or {}))
    
    def close(self):
        self.driver.close()
        
    def __enter__(self):
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close() 