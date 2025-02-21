import time
from rich.pretty import pprint
from net_graph import NetGraph
from dns_utils import eat_dns_file

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

    for domain_node in eat_dns_file(max=1):
        print("-----------------------")
        print("[+] processing domain_node: ", domain_node)
        ng.sync_domain_node(domain_node)

    print("\n=== All DomainNodes and DomainRelationships ===")
    pprint(ng.dump_nodes_with_rel())
    print("\n=== Everything in DB ===")
    pprint(ng.dump_all())

    print(f"[i] Number of domains: {ng.count_domain_node()}")
    print(f"[i] Number of relationships: {ng.count_domain_relationships()}")

    ng.close() 