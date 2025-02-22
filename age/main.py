import time
import sys
from rich.pretty import pprint
from net_graph import NetGraph
#from dns_reccord_node import DNSReccordNode 
from dns_utils import eat_dns_file, output_domains, eat_dnsr_file

def rm_db():
    ng = NetGraph()
    ng.delete()
    ng.close()
    time.sleep(1)  # Allow time for AGE/PostgreSQL cleanup

if __name__ == "__main__":


    if sys.argv[1] == "rm-db":
        rm_db()
        exit()
    
    if sys.argv[1] == "re-read-domains":
        rm_db()
        ng = NetGraph()

        print(f"[i] Number of domains: {ng.count_domain_node()}")
        print(f"[i] Number of relationships: {ng.count_domain_relationships()}")

        for domain_node in eat_dns_file(max=111):
            print("-----------------------")
            print("[+] processing domain_node: ", domain_node)
            ng.sync_domain_node(domain_node)

        print("\n=== All DomainNodes and DomainRelationships ===")
        pprint(ng.dump_domain_nodes_with_rel())
        print("\n=== Everything in DB ===")
        pprint(ng.dump_all())

        print(f"[i] Number of domains: {ng.count_domain_node()}")
        print(f"[i] Number of relationships: {ng.count_domain_relationships()}")
        ng.close() 

    if sys.argv[1] == "dump-domains":
        dom = ng.dump_domains_host()
        output_domains(dom)


    if sys.argv[1] == "re-read-dnsr":
        ng = NetGraph()
        for dnsr_node in eat_dnsr_file(max=111):
            print("-----------------------")
            #print("[+] processing dnsr_node: ", dnsr_node)
            ng.sync_dnsr_node(dnsr_node)

        ng.close()

