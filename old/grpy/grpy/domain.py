from .db import Neo4jDB

class DomainManager:
    def __init__(self, *, db):
        self.db = db
    
    def merge_domain(self, domain_name: str) -> dict:
        result = self.db.execute(
            "MERGE (d:Domain {name: $name}) RETURN d",
            {"name": domain_name}
        )
        return result["d"] if result else None

    def merge_link_domain_to_parent(self, domain_name: str, parent_name: str) -> dict:
        result = self.db.execute(
            "MERGE (d:Domain {name: $name})-[:PARENT]->(p:Domain {name: $parent_name}) RETURN d",
            {"name": domain_name,
            "parent_name": parent_name}
        )
        return result["d"] if result else None

    def merge_link_to_top(self, *, domain_name: str, top: str) -> None:
        self.db.execute(
            query="""
            MERGE (d:Domain {name: $domain})
            WITH d
            MERGE (t:Domain {name: $top})
            MERGE (d)-[:PART_OF]->(t)
            """,
            parameters={
                "domain": domain_name,
                "top": top
            }
        )

    def expand_paths(self, nodes: list) -> list:
        paths = []
        for i in range(len(nodes)):
            full_name = '.'.join(nodes[i:])
            paths.append(full_name)
        return paths
    
    def add_new_dns_root_ine(self, domain_base: str) -> list:
        result = self.db.execute(
                "MATCH (d:Domain {name: $name, entrypoint: true}) RETURN d limit 1",
                {"name": domain_base}
                )
        record = result

        if not record:
            print(f"adding new entrypoint: {domain_base}")
            result = self.db.execute(
            "MERGE (d:Domain {name: $name, entrypoint: true}) RETURN d",
            {"name": domain_base}
            )
            print(result["d"])
        else:
            print(f"NOT adding new entrypoint: {domain_base}") 