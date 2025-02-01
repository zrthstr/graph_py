import argparse
from .db import Neo4jDB
from .domain import DomainManager
from .dns_record import DNSrecordManager, DNSRecord

def ingest_file_dnsx(*, db: Neo4jDB, filename: str) -> None:
    """Ingest DNS data from dnsx file"""
    domain_mgr = DomainManager(db=db)
    record_mgr = DNSrecordManager(db=db)
    
    print(f"\nIngesting data from {filename}...")
    try:
        with open(filename) as f:
            for line in f:
                parts = line.strip().split(" [")
                if len(parts) != 3:
                    continue
                    
                domain = parts[0]
                record_type = parts[1].rstrip("]")
                value = parts[2].rstrip("]")
                
                print(f"Found: {domain} {record_type} {value}")
                
                domain_base = domain.split(".")[-1]
                domain_mgr.merge_link_to_top(domain_name=domain, top=domain_base)
                
                record = DNSRecord(name=domain, type_=record_type, values=[value])
                record_mgr.merge_record(record=record)
                
    except Exception as e:
        print(f"Error during ingestion: {e}")

def clear_data(*, db: Neo4jDB):
    """Clear all data from the database"""
    db.execute(query="MATCH (n) DETACH DELETE n")

def print_stats(*, db: Neo4jDB):
    """Print database statistics"""
    print("\nNode counts:")
    result = db.execute_many(
        query="""
        MATCH (n)
        WITH labels(n)[0] as type, count(*) as count
        RETURN type + ': ' + toString(count) as output
        ORDER BY count DESC
        """
    )
    
    for record in result:
        if isinstance(record, str):
            print(record)
        else:
            print(record.values()[0])
    
    print("\nRelationship counts:")
    rel_result = db.execute_many(
        query="""
        MATCH ()-[r]->()
        WITH type(r) as type, count(*) as count
        RETURN type + ': ' + toString(count) as output
        ORDER BY count DESC
        """
    )
    
    for record in rel_result:
        if isinstance(record, str):
            print(record)
        else:
            print(record.values()[0])

def setup_parser():
    parser = argparse.ArgumentParser(description='Graph DNS tool')
    subparsers = parser.add_subparsers(dest='command', help='Commands')

    subparsers.add_parser('clear', help='Clear all data')
    subparsers.add_parser('stats', help='Print database statistics')
    
    ingest_parser = subparsers.add_parser('ingest', help='Ingest DNS data')
    ingest_parser.add_argument('file', nargs='?', default='testdata/fefe.de.dnsx', help='File to ingest')
    ingest_parser.add_argument('--format', choices=['dnsx'], default='dnsx', 
                              help='Input file format')

    return parser

def main():
    parser = setup_parser()
    args = parser.parse_args()
    
    db = Neo4jDB(
        uri="bolt://localhost:7687",
        user="neo4j",
        password="neo4jneo4jneo4j"
    )

    if args.command == 'clear':
        clear_data(db=db)
    elif args.command == 'stats':
        print_stats(db=db)
    elif args.command == 'ingest':
        ingest_file_dnsx(db=db, filename=args.file)
    else:
        parser.print_help()
        return

    print(f"Command '{args.command}' completed successfully")

if __name__ == "__main__":
    main()