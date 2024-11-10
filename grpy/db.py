from neo4j import GraphDatabase
from typing import Optional, Dict, Any, List

class Neo4jDB():
    def __init__(self, uri: str, user: str, password: str):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
    
    def execute(self, query: str, params: Dict[str, Any] = None) -> Any:
        with self.driver.session() as session:
            result = session.run(query, parameters=params or {})
            return result.single() if result else None
            
    def execute_many(self, query: str, params: Dict[str, Any] = None) -> list:
        with self.driver.session() as session:
            result = session.run(query, parameters=params or {})
            return list(result)
    
    def close(self):
        self.driver.close()
        
    def __enter__(self):
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close() 