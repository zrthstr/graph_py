import json
import age
import time
from rich.pretty import pprint

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
    def __init__(self, host, _input, source, _id=None):
        self.host = host
        self.input = _input
        self.source = source
        self.id = _id
        
    def get_subdomain_chain(self):
        """Returns list of DomainNodes representing the subdomain hierarchy."""
        if self.is_root():
            print(f"[i] {self.host} is root domain")
            return []
            
        if not self.host.endswith(self.input):
            raise ValueError(f"Host {self.host} is not a subdomain of {self.input}")
            
        subdomain_part = self.host[:-len(self.input)-1]
        parts = subdomain_part.split('.')
        print(f"[i] subdomain parts for {self.host}: {parts}")
        
        # Build chain from right to left
        nodes = []
        current_parts = []
        for part in reversed(parts):
            current_parts.insert(0, part)
            full_subdomain = '.'.join(current_parts) + '.' + self.input
            # Mark intermediate nodes as implicit unless it's the final (original) domain
            source = self.source if full_subdomain == self.host else "implicit"
            nodes.append(DomainNode(full_subdomain, self.input, source))
            print(f"[i] created chain node: {full_subdomain} (source: {source})")
        return nodes

    @classmethod
    def from_age_vertex(cls, vertex, root_domain=None):
        """
        Create a DomainNode from an AGE vertex.
        
        Args:
            vertex: AGE vertex object
            root_domain: Optional root domain for input field
        """
        host = vertex.properties['host']
        source = vertex.properties.get('source', 'unknown')
        _input = root_domain if root_domain else host
        return cls(host=host, _input=_input, source=source, _id=vertex.id)

    def __repr__(self):
        return f"DomainNode(host={self.host}, input={self.input}, source={self.source})"

    def is_root(self):
        """Returns True if this node represents a root domain."""
        return self.host == self.input


def eat_dns_file(infile="../data/dns.out.jsonl",max=0):
    with open(infile, 'r') as f:
        for line in f:
            max -=1
            if max == 0:
                break
            try:
                data = json.loads(line.strip())
                domain_node = DomainNode(data['host'], data['input'], data['source'])
                #print(domain_node)
                yield domain_node
            except json.JSONDecodeError:
                print(f"Error decoding JSON: {line}")
            except KeyError as e:
                print(f"Missing field {e} in line: {line.strip()}")


class NetGraph:
    def __init__(self, graph_name="test_graph", dsn="host=localhost port=5455 dbname=postgresDB user=postgresUser password=postgresPW"):

        self.graph_name = graph_name
        ag = age.connect(graph=graph_name, dsn=dsn)
        self.conn = ag

    def close(self):
        print("[-] closing db")
        self.conn.close()

    def delete(self):
        """Delete the entire graph and commit the changes."""
        try:
            print(f"[-] Deleting graph '{self.graph_name}'")
            age.deleteGraph(self.conn.connection, self.graph_name)
            self.conn.commit()
            print("[+] Graph deleted successfully")
        except Exception as e:
            print(f"[!] Error deleting graph: {e}")
            raise

    def exist_domain_node(self, domain: DomainNode):
        ret = self.conn.execCypher("MATCH (d:Domain {host: %s}) RETURN 1 LIMIT 1", params=(domain.host,))
        return bool(ret.fetchone())

    def exist_identical_domain_node(self, domain: DomainNode):
        ret = self.conn.execCypher("MATCH (d:Domain {host: %s, source: %s}) RETURN id(d)",params=(domain.host, domain.source))
        return bool(ret.fetchone())

    def insert_domain_node(self, domain: DomainNode):
        print(f"[+] inserting domain_node: {domain}")
        
        # First ensure root domain exists
        print(f"[+] ensuring root domain exists: {domain.input}")
        query = """
            MERGE (r:DomainRoot {host: %s})
            RETURN r
        """
        self.conn.execCypher(query, params=(domain.input,))
        self.conn.commit()
        
        # If this is just a root domain, we're done
        if domain.is_root():
            return True
            
        # Get and insert the subdomain chain
        chain = domain.get_subdomain_chain()
        for i, subdomain in enumerate(chain):
            parent_host = domain.input if i == 0 else chain[i-1].host
            print(f"[+] creating/linking: {subdomain.host} -> parent: {parent_host}")
            
            query = """
            MATCH (p {host: %s})
            MERGE (d:Domain {host: %s, source: %s})
            MERGE (p)-[:HAS_SUBDOMAIN]->(d)
            RETURN d
            """
            self.conn.execCypher(query, params=(parent_host, subdomain.host, subdomain.source))
            self.conn.commit()

    def exists_domain_root_node(self, domain: DomainNode):
        ret = self.conn.execCypher("MATCH (r:DomainRoot {host: %s}) RETURN id(r)", params=(domain.input,))
        return bool(ret.fetchone())

    def ifnonex_insert_domain_root_node(self, domain: DomainNode):
        print("[+] inserting domain root node if nonexistant")
        if self.exists_domain_root_node(domain):
            print("[i] domain root node found, skipping")
            return
        ret = self.conn.execCypher("CREATE (r:DomainRoot {host: %s}) RETURN id(r)", params=(domain.input,))
        ret_id = ret.fetchone()
        self.conn.commit()
        print(f"[+] inserted new DomainRoot {ret_id}")
        return ret_id


    def count_domain_node(self):
        ret = self.conn.execCypher("MATCH (n:Domain) RETURN COUNT(DISTINCT n.host) ")
        return ret.fetchone()[0]

    def sync_domain_node(self, domain: DomainNode):
        print(f"[i] processing domainNode: {domain}")
        if self.exist_domain_node(domain):
            if self.exist_identical_domain_node(domain):
                print("[i] domain node exists with same attribiutes")
                return
            else:
                print("[i] domain node exsists but with other attribiutes")
                raise Exception("Not implemented")
                ## merge nodes!
                return
        print("[i] domain_node not found")
        self.insert_domain_node(domain)
        return

    def get_all_domain_nodes_and_rel(self):
        query = """
        MATCH (r:DomainRoot)-[:CONNECTED_TO]->(d:Domain)
        RETURN r.host AS root_name, d.host AS domain_host
        """
        pass

    def dump_nodes(self):
        query = "MATCH (n) RETURN n"
        ret = self.conn.execCypher(query)
        return ret.fetchall()

    def dump_nodes_with_rel(self):
        """Raw dump of nodes with relationships from the database."""
        query = """
        MATCH path=(root:DomainRoot)-[:HAS_SUBDOMAIN*]->(sub:Domain)
        WHERE sub.source <> 'implicit'
        RETURN root, RELATIONSHIPS(path), sub, NODES(path)
        """
        ret = self.conn.execCypher(query, cols=["root AGTYPE", "rels AGTYPE", "sub AGTYPE", "nodes AGTYPE"])
        return ret.fetchall()

    def dump_nodes_with_rel_as_objects(self):
        """Convert database dump to domain objects."""
        raw_data = self.dump_nodes_with_rel()
        result = []
        for row in raw_data:
            root, rels, sub, nodes = row
            root_node = DomainNode.from_age_vertex(root)
            sub_node = DomainNode.from_age_vertex(sub, root_domain=root_node.host)
            result.append((root_node, rels, sub_node))
        return result

    def dump_everything(self):
        # Get all paths in the graph
        query = """
        MATCH (n)-[r]->(m)
        RETURN n, r, m
        """
        ret = self.conn.execCypher(query, cols=["node1 AGTYPE", "rel AGTYPE", "node2 AGTYPE"])
        return ret.fetchall()

def rm_db():
    ng = NetGraph()
    ng.delete()
    ng.close()
    time.sleep(1)


if __name__ == "__main__":
    rm_db()

    ng = NetGraph()

    print("[i] Number of domains: ", ng.count_domain_node())

    for domain_node in eat_dns_file(max=10):
        #ng.sync_domain_node(domain_node)
        #ng.insert_domain_node(domain_node)
        ng.sync_domain_node(domain_node)

    #a = ng.get_all_domain_nodes_and_rel()

    pprint(ng.dump_nodes())
    print("\n=== All Relationships ===")
    pprint(ng.dump_nodes_with_rel())
    #print("\n=== Everything in DB ===")
    #pprint(ng.dump_everything())

    print("[i] Number of domains: ", ng.count_domain_node())

    ng.close()
