import json
from itertools import islice
from domain_node import DomainNode

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