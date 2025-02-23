import time
import sys
from rich.pretty import pprint
from net_graph import NetGraph
#from dns_reccord_node import DNSReccordNode 
from dns_utils import eat_dns_file, output_domains, eat_dnsr_file, eat_dnsr_cmd

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
        ng = NetGraph()
        dom = ng.dump_domains_host()
        output_domains(dom)
        ng.close()

    if sys.argv[1] == "delete-all-dnsr-nodes":
        ng = NetGraph()
        ng.delete_all_dnsr_nodes()
        ng.close()

    if sys.argv[1] == "re-read-dnsr":
        ng = NetGraph()
        for dnsr_node in eat_dnsr_file(max=111):
            print("-----------------------")
            #print("[+] processing dnsr_node: ", dnsr_node)
            ng.sync_dnsr_node(dnsr_node)
            
        all_domains_tried = eat_dnsr_cmd()
        for domain in all_domains_tried:
            status = ng.mark_dnsr_node_as_tried(domain)
            ng.conn.commit()
            if status == "not_found":
                print(f"[i] DNSr {domain} in command but no entries found, marking as tried")
            else:
                print(f"[i] DNSr {domain} skipped")

        pprint(ng.dump_dnsr_nodes_with_status_code())

        print("--------------------------------")
        pprint(ng.dump_dnsr_nodes_with_rel())


        ng.close()

    ng = NetGraph()
    pprint(ng.dump_dnsr_nodes_with_status_code())
    ng.close()