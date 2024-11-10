from pathlib import Path
from neo4j import GraphDatabase
from typing import Optional, Dict, Any, List, Literal
from dataclasses import dataclass, field




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
            raise(f"tryig to merge dns records of differnet types: {type_} and {new_type_}") 
        values = list(set( values + new_values ))



class DNSrecordManager:
    def __init__(self, db: Neo4jDB):
        self.db = db

    def merge_record(self, record: DNSRecord):
        # read, then if exists merge records in python
        # write back either way 

        result = db.execute("MATCH (a:DNSR {name: $name, type: $type}) RETURN a",
            {"name": record.name, "type": record.type_})


        if result:  # Record already exists, merge values
            assert len(result) == 1
            existing_record = result[0]
            print("Existing record:", existing_record["name"], existing_record["type"], existing_record["values"])
        
            values = list(set(existing_record["values"] + record.values))
            new_record = DNSRecord(name=existing_record["name"], values=values, type_=existing_record["type"])
            db.execute("MERGE (a:DNSR {name: $name, type: $type}) SET a.values = $values",
                   {"name": new_record.name, "type": new_record.type_, "values": new_record.values})

        else:  # Record does not exist, insert a new one
            #db.execute("CREATE (a:DNSR {name: $name, type: $type, values: $values})",
            #       {"name": record.name, "type": record.type_, "values": record.values})

            db.execute("""
                MATCH (d:Domain {name: $name})
                CREATE (d)-[:HAS]->(a:DNSR {name: $name, type: $type, values: $values})""",
                {"name": record.name, "type": record.type_, "values": record.values})




class DomainManager:
    def __init__(self, db: Neo4jDB):
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


    def merge_link_to_top2(self, domain_name, top) -> dict:
        ## we need to do it this strangly to aavoid linking TLDs with "." to each other
        ## e.g: ibar.foo.co.uk -> [ibar, foo, co.uk] not [ibar foo, co, uk]
        assert(domain_name.endswith(top))
        assert(domain_name != top)
        domain_name = domain_name[:-len(top)].rstrip('.')
        s = domain_name.split(".") + [top]
        count = len(domain_name.split("."))

        print(count)
        print(s)
        assert(count > 1)
        
        for e in range(count):
            print(f"link e:{e} {s[e]} -> {s[e+1]}")
            self.merge_link_domain_to_parent(s[e],s[e+1])


    def merge_link_to_top(self, domain_name, top) -> dict:
        assert(domain_name.endswith(top))
        assert(domain_name != top)
        domain_name = domain_name[:-len(top)].rstrip('.')
        s = domain_name.split(".") + [top]
        count = len(domain_name.split("."))
        #print(count)
        print(s)
        s=self.expand_paths(s)
        print(s)
        #assert(count > 1)

        ret = self.db.execute(
        """
        UNWIND range(0, size($path) - 2) AS i
        MERGE (n1:Domain {name: $path[i]})
        MERGE (n2:Domain {name: $path[i + 1]})
        MERGE (n1)-[:REL]->(n2)
        """, {"path": s}
        )  
        print("ret:", ret)      
    #print("retF:", ret["firstNodeId"])      


        # TBD: now set "root"

        # also set DNS RECORD, as object, conaining list
        #  first check if exists, so we know if we just add dns?
        # load the list, add new entry, make set, and insert as list



    def expand_paths(self, nodes: list) -> list:
        paths = []
        for i in range(len(nodes)):
            full_name = '.'.join(nodes[i:])  # Create full name from current index to end
            paths.append(full_name)
        return paths
    
    ## ... if not exists
    def add_new_dns_root_ine(self, domain_base: str) -> list:
        result = db.execute(
                "MATCH (d:Domain {name: $name, entrypoint: true}) RETURN d limit 1",
                {"name": domain_base}
                )
        record = result

        if not record:
            print(f"adding new entrypoint: {domain_base}")
            result = db.execute(
            "MERGE (d:Domain {name: $name, entrypoint: true}) RETURN d",
            {"name": domain_base}
            )
            print(result["d"])
        else:
            print(f"NOT adding new entrypoint: {domain_base}")



def ingest_file_dnsx(db: Neo4jDB, in_file_name: str):
    lines = (line.strip() for line in open(in_file_name))
    domain_mgr = DomainManager(db)
    dns_mgr = DNSrecordManager(db)

    domain_base = ".".join(in_file_name.split('/')[-1].split(".")[:-1])

    ## does not seem neccary anymore
    # domain_mgr.add_new_dns_root_ine(domain_base)


    for line in lines:
        domain, record_type, record_value = line.split()
        record_type = record_type[1:-1]
        record_value = record_value[1:-1]

        try:
            dns_record = DNSRecord(name=domain, values=[record_value], type_=record_type)
            #print(dns_record.name)   # Output: Alice
            #print(dns_record.values) # Output: [1, 2, 3]
            #print(dns_record.type_)  # Output: FOO
        except ValueError as e:
            print(e)
            exit()

        dns_mgr.merge_record(dns_record)
        domain_mgr.merge_link_to_top(domain, domain_base)

        #exit()


        # a = domain_mgr.merge_link_domain_to_parent("new.fefe.deee","fefe.deee")
    #print(a)
    #a = domain_mgr.merge_link_to_top("aaaa.bbbb.cccc.new.fefe.deee","fefe.deee")
    #a = domain_mgr.merge_link_to_top("jdijdijdi.bbbb.cccc.new.fefe.deee","fefe.deee")
    #a = domain_mgr.merge_link_to_top("jdijdijdi.bbbb.cc33.new.fefe.deee","fefe.deee")
    #print(a)


if __name__ == "__main__":
    db = Neo4jDB(
        uri="neo4j://localhost:7687",
        user="neo4j",
        password="neo4jneo4jneo4j"
    )
    
    domain_mgr = DomainManager(db)
    domain = domain_mgr.merge_domain("example.com")
    print(domain)

    ingest_file_dnsx(db,'testdata/fefe.de.dnsx')