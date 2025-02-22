import age
from rich.pretty import pprint
from domain_node import DomainNode
from dns_reccord_node import DNSReccordNode
from dns_utils import get_parent_domain_naive

class NetGraph:
    def __init__(self, graph_name="test_graph", dsn="host=localhost port=5455 dbname=postgresDB user=postgresUser password=postgresPW"):
        self.graph_name = graph_name
        self.conn = age.connect(dsn=dsn, graph=self.graph_name)


    def sync_dnsr_node(self, dnsr: DNSReccordNode):
        print("[DEBUG] Processing dnsr:")
        pprint(dnsr)

        self._create_all_dnsr_nodes(dnsr)
        self._create_all_dnsr_relationships(dnsr)
        self.conn.commit()

    def _create_all_dnsr_nodes(self, dnsr: DNSReccordNode):
        self.conn.execCypher("""
            MERGE (d:DNSReccord {host: %s})
            SET d.timestamp = %s,
                d.status_code = %s
        """, params=(dnsr.host, dnsr.timestamp, dnsr.status_code))
        print(f"[+] Created dnsr node: {dnsr.host}")


    def _create_all_dnsr_relationships(self, dnsr: DNSReccordNode):
        self.conn.execCypher("""
            MATCH (d:DNSReccord {host: %s})
            MATCH (r:Domain {host: %s})
            MERGE (r)-[:HAS_DNSR]->(d)
        """, params=(dnsr.host, dnsr.host))
        print(f"[+] Created dnsr relationship: {dnsr.host}")

    def sync_domain_node(self, domain: DomainNode):
        """Synchronize a domain and its implicit parent chain to the graph database."""
        print("[DEBUG] Processing domain chain:")
        implicit_nodes = domain.get_implicit_nodes()
        pprint(implicit_nodes)
        
        self._create_all_domain_nodes(implicit_nodes)
        self._create_all_domain_relationships(implicit_nodes)
        self.conn.commit()

    def _create_all_domain_nodes(self, domains):
        """Create all domain nodes in the database."""
        for index, domain in enumerate(domains):
            domain.is_implicit = index > 0  # First node is not implicit
            domain.is_root = domain.host == domain.input
            print(f"[+] Creating node: {domain}")
            
            self.conn.execCypher("""
                MERGE (d:Domain {host: %s})
                SET d.source = %s,
                    d.is_implicit = %s,
                    d.is_root = %s,
                    d.input = %s
            """, params=(
                domain.host,
                domain.source,
                domain.is_implicit,
                domain.is_root,
                domain.input
            ))

    def _create_all_domain_relationships(self, domains):
        """Create parent-child relationships between domain nodes."""
        for domain in domains:
            if not domain.is_root:
                parent = get_parent_domain_naive(domain.host)
                print(f"[+] Creating relationship: {parent} -> {domain.host}")
                
                self.conn.execCypher("""
                    MATCH (root:Domain {host: %s})
                    MATCH (sub:Domain {host: %s})
                    MERGE (root)-[:HAS_SUBDOMAIN]->(sub)
                """, params=(parent, domain.host))

    def count_domain_node(self):
        query = "MATCH (d:Domain) RETURN count(d)"
        result = self.conn.execCypher(query).fetchone()
        return result[0]

    def count_domain_relationships(self) -> int:
        query = "MATCH ()-[r:HAS_SUBDOMAIN]->() RETURN count(r) as count"
        return self.conn.execCypher(query).fetchone()[0]

    def dump_all(self):
        query = """
        MATCH (n)
        OPTIONAL MATCH (n)-[r]->(m)
        RETURN n as source, type(r) as relationship, m as target
        """
        return self.conn.execCypher(query, cols=["source", "relationship", "target"]).fetchall()
    
    def dump_dnsr_nodes_with_rel(self):
        query = """
        MATCH (n:DNSReccord)
        MATCH (m:Domain)-[r:HAS_DNSR]->(n)
        RETURN n as dnsr_node, r as relationships, m as domain_node
        """
        return self.conn.execCypher(query, cols=["dnsr_node", "relationships", "domain_node"]).fetchall()

    def dump_domain_nodes_with_rel(self):
        query = """
        MATCH (n:Domain)
        MATCH (n)-[r:HAS_SUBDOMAIN]->(m:Domain)
        RETURN n as root_node, r as relationships, m as sub_node
        """
        return self.conn.execCypher(query, cols=["root_node", "relationships", "sub_node"]).fetchall()

    def dump_domains_host(self):
        query = "MATCH (d:Domain) RETURN d.host"
        back = self.conn.execCypher(query, cols=["d"]).fetchall()
        return [t[0] for t in back]
    
    def delete(self):
        age.deleteGraph(self.conn.connection, self.graph_name)
        self.conn.commit()

    def close(self):
        self.conn.close() 