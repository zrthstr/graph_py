import json
import age
import time
from rich.pretty import pprint
from itertools import islice

#import psycopg2

"""
Graph Database Project for IT Infrastructure Mapping

A tool to map and analyze IT infrastructure components including:
- Servers
- Domains and subdomains
- DNS records
- Networks and interfaces
- Virtual hosts
- Directories and web roots
- Load balancers
- CGI endpoints

Currently implemented using Apache AGE on PostgreSQL.

Data Collection:
The system ingests data from various security and network scanning tools including:
- subfinder
- dnsx
- nmap
- masscan
- dnsenum
- dnsrecon

Implementation:
Data from these tools is stored in a directory-based structure and processed
by this Python script using a ledger-style approach for consistent tracking
and historical records.
"""

class DomainNode:
    def __init__(self, host, _input, source, is_implicit=False, is_root=False):
        self.host = host
        self.input = _input
        self.source = source
        self.is_implicit = is_implicit
        self.is_root = False

    #def is_root(self):
    #   return self.host == self.input
    
    def get_implicit_nodes(self):
        # Skip the first part as it's our actual domain
        # and avoid spliting the root (if the root itself contains dots)   
        parts = self.host.split('.')
        root_parts = self.input.split('.')
        subdomain_parts = parts[:-len(root_parts)] + [".".join(root_parts)]

        return [
            DomainNode(".".join(subdomain_parts[i:]), self.input, "implicit")
            for i in range(len(subdomain_parts))
        ]
    

    def get_node_DB_status(self):
        """ can return:
        implicit
        not_in_db
        in_db
        """
        pass

        
    @classmethod
    def from_age_vertex(cls, vertex, root_domain=None):
        host = vertex.properties['host']
        source = vertex.properties.get('source', 'unknown')
        _input = root_domain if root_domain else host
        is_root = vertex.properties.get('is_root', False)
        is_implicit = vertex.properties.get('is_implicit', False)
        return cls(host=host, _input=_input, source=source, is_implicit=is_implicit, is_root=is_root)

    def __repr__(self):
        return f"DomainNode(host={self.host}, input={self.input}, source={self.source}, is_implicit={self.is_implicit}, is_root={self.is_root})"

def get_parent_domain_naive(domain: str) -> str:
    """Get the immediate parent domain by removing leftmost part.
    This function is naive, it does not handle multi levels TLDS
    
    Examples:
        foo.bar.com -> bar.com
        bar.com -> com
        com -> raises ValueError

    """
    parts = domain.split('.')
    if len(parts) < 2:
        raise ValueError(f"Domain {domain} has no parent")
    return '.'.join(parts[1:])

def eat_dns_file(infile="../data/dns.out.jsonl", max=0):
    with open(infile, 'r') as f:
        lines = islice(f, max) if max > 0 else f
        for line in lines:
            try:
                data = json.loads(line.strip())
                yield DomainNode(data['host'], data['input'], data['source'])
            except json.JSONDecodeError:
                print(f"Error decoding JSON: {line}")
            except KeyError as e:
                print(f"Missing field {e} in line: {line.strip()}")


class NetGraph:
    def __init__(self, graph_name="test_graph", dsn="host=localhost port=5455 dbname=postgresDB user=postgresUser password=postgresPW"):
        self.graph_name = graph_name
        self.conn = age.connect(dsn=dsn, graph=self.graph_name)

    def insert_domain_node(self, domain: DomainNode):
        """Insert a domain node and its relationships into the graph."""
        if domain.host == domain.input:
            print("///////////////////////// ROOOOT")
            domain.is_root = True

        print(f"[+] Inserting domain node: {domain}")
        pprint(domain)
            
        # Then create/update the subdomain
        node_query = """
            MERGE (d:Domain {host: %s})
            SET d.source = %s,
                d.is_implicit = %s,
                d.is_root = %s
        """
        self.conn.execCypher(
            node_query,
            params=(
                domain.host,
                domain.source,
                domain.is_implicit,
                domain.is_root
            )
        )
        
        if not domain.is_root:
            ## we can be naive here, as we know get_implicit_nodes() does the thinking for us
            parent = get_parent_domain_naive(domain.host)
            print(f"[+] Creating relationship for {domain.host} -> {parent}")
            rel_query = """
            MATCH (root:Domain {host: %s})
            MATCH (sub:Domain {host: %s})
            MERGE (root)-[:HAS_SUBDOMAIN]->(sub)
            """
            self.conn.execCypher(rel_query, params=(parent, domain.host))
        
        self.conn.commit()

    def sync_domain_node(self, domain: DomainNode):
        """Sync a domain node with the graph."""
        for domain_implicit in domain.get_implicit_nodes():
            domain_implicit.is_implicit = True
            print(f"[+] Inserting implicit domain: {domain_implicit}")
            self.insert_domain_node(domain_implicit)
        print(f"[+] Inserting explicit domain: {domain}")
        self.insert_domain_node(domain)

    def count_domain_node(self):
        """Count all domain nodes."""
        query = "MATCH (d:Domain) RETURN count(d)"
        result = self.conn.execCypher(query).fetchone()
        return result[0]

    def count_domain_relationships(self) -> int:
        """Count the total number of relationships in the graph."""
        query = "MATCH ()-[r:HAS_SUBDOMAIN]->() RETURN count(r) as count"
        return self.conn.execCypher(query).fetchone()[0]

    def dump_all(self):
        """Get everything in the database."""
        query = """
        MATCH (n)
        OPTIONAL MATCH (n)-[r]->(m)
        RETURN n as source, type(r) as relationship, m as target
        """
        return self.conn.execCypher(query, cols=["source", "relationship", "target"]).fetchall()

    def dump_nodes_with_rel(self):
        """Get all domain nodes and their relationships."""
        query = """
        MATCH (n:Domain)
        OPTIONAL MATCH (n)-[r:HAS_SUBDOMAIN]->(m:Domain)
        RETURN n as root_node, r as relationships, m as sub_node
        """
        return self.conn.execCypher(query, cols=["root_node", "relationships", "sub_node"]).fetchall()
    
    def delete(self):
        """Delete the graph."""
        age.deleteGraph(self.conn.connection, self.graph_name)
        self.conn.commit()

    def close(self):
        """Close the database connection."""
        self.conn.close()

def rm_db():
    ng = NetGraph()
    ng.delete()
    ng.close()
    time.sleep(1)  # Allow time for AGE/PostgreSQL cleanup


if __name__ == "__main__":
    rm_db()

    ng = NetGraph()

    print(f"[i] Number of domains: {ng.count_domain_node()}")
    print(f"[i] Number of relationships: {ng.count_domain_relationships()}")

    for domain_node in eat_dns_file(max=10):
        #ng.sync_domain_node(domain_node)
        #ng.insert_domain_node(domain_node)
        print("-----------------------")
        ng.sync_domain_node(domain_node)

    #a = ng.get_all_domain_nodes_and_rel()

    #pprint(ng.dump_nodes())
    print("\n=== All DomainNodes and DomainRelationships ===")
    pprint(ng.dump_nodes_with_rel())
    print("\n=== Everything in DB ===")
    pprint(ng.dump_all())

    print(f"[i] Number of domains: {ng.count_domain_node()}")
    print(f"[i] Number of relationships: {ng.count_domain_relationships()}")

    ng.close()
