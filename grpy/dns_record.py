from typing import List, Literal
from dataclasses import dataclass
from .db import Neo4jDB

@dataclass
class DNSRecord:
    name: str
    values: List[str]
    type_: Literal['A', 'AAAA', 'CNAME', 'SOA', 'NS', 'TXT', 'SRV', 'PTR', 'CAA', 'AXFR']

    def __post_init__(self):
        if not isinstance(self.values, list):
            raise ValueError("values must be a list")

    def add_record(self, new_type_, new_values):
        if not new_type_ == type_:
            raise(f"trying to merge dns records of different types: {type_} and {new_type_}") 
        values = list(set(values + new_values))

class DNSrecordManager:
    def __init__(self, db: Neo4jDB):
        self.db = db

    def merge_record(self, record: DNSRecord):
        result = self.db.execute("MATCH (a:DNSR {name: $name, type: $type}) RETURN a",
            {"name": record.name, "type": record.type_})

        if result:  # Record already exists, merge values
            assert len(result) == 1
            existing_record = result[0]
            print("Existing record:", existing_record["name"], existing_record["type"], existing_record["values"])
        
            values = list(set(existing_record["values"] + record.values))
            new_record = DNSRecord(name=existing_record["name"], values=values, type_=existing_record["type"])
            self.db.execute("MERGE (a:DNSR {name: $name, type: $type}) SET a.values = $values",
                   {"name": new_record.name, "type": new_record.type_, "values": new_record.values})

        else:  # Record does not exist, insert a new one
            self.db.execute("""
                MATCH (d:Domain {name: $name})
                CREATE (d)-[:HAS]->(a:DNSR {name: $name, type: $type, values: $values})""",
                {"name": record.name, "type": record.type_, "values": record.values})