import age
from rich.pretty import pprint
from domain_node import DomainNode
from dns_utils import get_parent_domain_naive

class NetGraph:
    def __init__(self, graph_name="test_graph", dsn="host=localhost port=5455 dbname=postgresDB user=postgresUser password=postgresPW"):
        self.graph_name = graph_name
        self.conn = age.connect(dsn=dsn, graph=self.graph_name)

    def insert_domain_node(self, domain: DomainNode):
        if domain.host == domain.input:
            domain.is_root = True

        print(f"[++] domain: {domain}")
        pprint(domain)
            
        node_query = """
            MERGE (d:Domain {host: %s})
            SET d.source = %s,
                d.is_implicit = %s,
                d.is_root = %s,
                d.input = %s
        """
        self.conn.execCypher(
            node_query,
            params=(
                domain.host,
                domain.source,
                domain.is_implicit,
                domain.is_root,
                domain.input
            )
        )
        
        self.conn.commit()

    def link_domain_node(self, domain: DomainNode):
        if domain.host == domain.input:
            domain.is_root = True
        print(f"[++] domainLink: {domain}")
        pprint(domain)

        if not domain.is_root:
            parent = get_parent_domain_naive(domain.host)
            print(f"[++] relationship for {parent} -> {domain.host}")
            rel_query = """
            MATCH (root:Domain {host: %s})
            MATCH (sub:Domain {host: %s})
            MERGE (root)-[:HAS_SUBDOMAIN]->(sub)
            """
            d = self.conn.execCypher(rel_query, params=(parent, domain.host)).fetchone()
            print("DEBUG: ", d)
        
        self.conn.commit()

        pass

    def sync_domain_node(self, domain: DomainNode):

        print("[DEBUG] domain_chain: ")
        pprint(domain.get_implicit_nodes())
        no_first = False
        for domain_implicit in domain.get_implicit_nodes():
            domain_implicit.is_implicit = no_first
            no_first = True
            print(f"[+] Inserting domain: {domain_implicit}")
            self.insert_domain_node(domain_implicit)

        no_first = False
        for d in domain.get_implicit_nodes():
            d.is_implicit = no_first
            print(f"[+] Linking domains: {d}")
            self.link_domain_node(d)





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

    def dump_nodes_with_rel(self):
        query = """
        MATCH (n:Domain)
        OPTIONAL MATCH (n)-[r:HAS_SUBDOMAIN]->(m:Domain)
        RETURN n as root_node, r as relationships, m as sub_node
        """
        return self.conn.execCypher(query, cols=["root_node", "relationships", "sub_node"]).fetchall()

    def dump_nodes_with_rel_as_objects(self):
        nodes = self.dump_nodes_with_rel()
        return [
            (DomainNode.from_age_vertex(node[0]),
             node[1],
             DomainNode.from_age_vertex(node[2]) if node[2] else None)
            for node in nodes
        ]
    
    def delete(self):
        age.deleteGraph(self.conn.connection, self.graph_name)
        self.conn.commit()

    def close(self):
        self.conn.close() 