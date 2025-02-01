from dataclasses import dataclass
from typing import List

DOMAIN_RECORD_TYPES = {'CNAME', 'MX', 'NS', 'SOA'}
IP_RECORD_TYPES = {'A', 'AAAA'}

@dataclass
class DNSRecord:
    name: str
    type_: str
    values: List[str]

class DNSrecordManager:
    def __init__(self, *, db):
        self.db = db

    def merge_record(self, *, record: DNSRecord) -> None:
        if record.type_ in IP_RECORD_TYPES:
            for value in record.values:
                self.db.execute(
                    query="""
                    MERGE (ip:IP {address: $value})
                    WITH ip
                    MATCH (d:DNSR {name: $name})
                    MERGE (d)-[r:$type]->(ip)
                    """,
                    parameters={
                        "name": record.name,
                        "type": record.type_,
                        "value": value
                    }
                )
        elif record.type_ in DOMAIN_RECORD_TYPES:
            for value in record.values:
                self.db.execute(
                    query="""
                    MERGE (target:Domain {name: $value})
                    WITH target
                    MATCH (d:DNSR {name: $name})
                    MERGE (d)-[r:$type]->(target)
                    """,
                    parameters={
                        "name": record.name,
                        "type": record.type_,
                        "value": value
                    }
                )
        else:
            # Handle other record types (TXT, etc) - for now just store as property
            self.db.execute(
                query="""
                MATCH (d:DNSR {name: $name})
                SET d[$type] = $values
                """,
                parameters={
                    "name": record.name,
                    "type": record.type_,
                    "values": record.values
                }
            )