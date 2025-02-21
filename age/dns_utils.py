import json
from itertools import islice
from domain_node import DomainNode
from dns_reccord_node import DNSReccordNode

def get_parent_domain_naive(domain: str) -> str:
    """Get the immediate parent domain by removing leftmost part.
    This function is naive, it does not handle multi levels TLDS
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


def eat_dnsr_file(infile="../data/dnsr.out.jsonl", max=0):
    with open(infile, 'r') as f:
        lines = islice(f, max) if max > 0 else f
        for line in lines:
            try:
                data = json.loads(line.strip())
                # Create the main domain node with required host field
                if 'host' not in data:
                    print(f"Skipping record - no host field: {line.strip()}")
                    continue
                    
                domain = DNSReccordNode(
                    host=data['host'],
                    status_code=data.get('status_code'),
                    a=data.get('a', []),
                    aaaa=data.get('aaaa', []),
                    mx=data.get('mx', []),
                    ns=data.get('ns', []),
                    txt=data.get('txt', []),
                    cname=data.get('cname', []),
                    soa=data.get('soa', []),
                    ptr=data.get('ptr', []),
                    spf=data.get('spf', []),
                    dkim=data.get('dkim', []),
                    dmarc=data.get('dmarc', [])
                )
                
                yield domain
                
            except json.JSONDecodeError:
                print(f"Error decoding JSON: {line}")




def output_domains(domains_text: list[str], filename: str = "../out/dns.txt"):
    with open(filename, "w") as f:
        f.write("\n".join(set(domains_text))+"\n")
