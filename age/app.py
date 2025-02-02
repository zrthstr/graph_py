import json
import age

#import psycopg2


class DomainNode:
    def __init__(self, host, _input, source):
        self.host = host
        self.input = _input
        self.source = source

    def __repr__(self):
        return f"domain_node(host={self.host}, input={self.input}, source={self.source})"


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
        print("[-] RM'ing db")
        age.deleteGraph(self.conn.connection, self.graph_name)
        #self.close()

    def exist_domain_node(self, domain: DomainNode):
        ret = self.conn.execCypher("MATCH (d:Domain {host: %s}) RETURN 1 LIMIT 1", params=(domain.host,))
        return bool(ret.fetchone())

    def exist_identical_domain_node(self, domain: DomainNode):
        ret = self.conn.execCypher("MATCH (d:Domain {host: %s, source: %s}) RETURN id(d)",params=(domain.host, domain.source))
        return bool(ret.fetchone())

    def insert_domain_node(self, domain: DomainNode):
        print("[+] inserting domain_node")
        self.ifnonex_insert_domain_root_node( domain)
        #ret = self.conn.execCypher("CREATE (d:Domain {host: %s, source: %s}) RETURN id(d)",params=(domain.host,domain.source))
        #ret_id = ret.fetchone()


        query = """
            MATCH (r:DomainRoot {host: %s})
            CREATE (d:Domain {host: %s, source: %s})
            CREATE (r)-[:CONNECTED_TO]->(d)
            RETURN id(d)
            """
        ret = self.conn.execCypher(query, params=(domain.input, domain.host, domain.source))
        ret_id = ret.fetchone()
        print(f"[+] inserted with id {ret_id}")

        self.conn.commit()
        return ret_id

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

        query = """
        MATCH (r:DomainRoot)-[:CONNECTED_TO]->(d:Domain)
        RETURN r.host, d.host
        """
        cursor = self.conn.execCypher(query, cols=["root_name VARCHAR", "domain_host VARCHAR"])
        return cursor.fetchall()  # Returns list of (root_name, domain_host)


if __name__ == "__main__":
    ng = NetGraph()

    print("[i] Number of domains: ", ng.count_domain_node())

    for domain_node in eat_dns_file(max=10):
        #ng.sync_domain_node(domain_node)
        #ng.insert_domain_node(domain_node)
        ng.sync_domain_node(domain_node)

    #a = ng.get_all_domain_nodes_and_rel()

    print(ng.dump_nodes())
    print("-" * 12)
    print(ng.dump_nodes_with_rel())

    print("[i] Number of domains: ", ng.count_domain_node())

    #ng.delete()
    ng.close()
