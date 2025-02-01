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
        ret = self.conn.execCypher("MATCH (n:Domain {host: %s}) RETURN 1 LIMIT 1", params=(domain.host,))
        return bool(ret.fetchone())

    def exist_identical_domain_node(self, domain: DomainNode):
        ret = self.conn.execCypher("MATCH (n:domain {host: %s, source: %s}) RETURN 1 LIMIT 1",params=(domain.host, domain.source))
        return bool(ret.fetchone())

    def insert_domain_node(self, domain: DomainNode):
        print("[+] inserting domain_node")
        ret = self.conn.execCypher("CREATE (d:Domain {host: %s, source: %s}) RETURN id(d)",params=(domain.host,domain.source))
        ret_id = ret.fetchone()
        print(f"[+] inserted with id {ret_id}")

        ###### I just do not fucking know if i need to commit
        #self.conn.commit()
        return ret_id

    def count_domain_node(self):
        ret = self.conn.execCypher("MATCH (n:Domain) RETURN COUNT(DISTINCT n.host) ")
        return ret.fetchone()[0]

    def sync_domain_node(self, domain: DomainNode):
        print(f"[i] processing domainNode: {domain}")
        if self.exist_domain_node(domain):
            if self.exist_identical_domain_node(domain):
                print("[i] domain node exists with same attribiutes")
                # noting to do
                return
            else:
                print("[i] domain node exsists but with other attribiutes")
                # update source  // merge domain nodes
                return
        print("[i] domain_node not found")
        self.insert_domain_node(domain)
        return


if __name__ == "__main__":
    ng = NetGraph()

    print("[i] Number of domains: ", ng.count_domain_node())

    for domain_node in eat_dns_file(max=10):
        #ng.sync_domain_node(domain_node)
        #ng.insert_domain_node(domain_node)
        ng.sync_domain_node(domain_node)


    print("[i] Number of domains: ", ng.count_domain_node())

    ng.delete()
    ng.close()
