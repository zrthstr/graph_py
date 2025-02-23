import networkx as nx
from pyvis.network import Network
from IPython.display import HTML, display
from datetime import datetime
from rich.pretty import pprint


def _create_domain_graph(graph_data):
    """Helper function to create the NetworkX graph structure for domain hierarchy."""
    G = nx.DiGraph()
    
    # Process each tuple in the data
    for root_vertex, edge, sub_vertex in graph_data:
        root_host = root_vertex.properties['host']
        root_is_root = root_vertex.properties['is_root']
        
        # Add root node
        G.add_node(root_host, is_root=root_is_root)
        
        # If we have both edge and sub_vertex, add the relationship
        if edge and sub_vertex:
            sub_host = sub_vertex.properties['host']
            G.add_node(sub_host, is_root=False)
            G.add_edge(root_host, sub_host)
    
    return G

def _visualize_network(G):
    """Helper function to create an interactive visualization from a NetworkX graph."""
    net = Network(notebook=True, height='700px', width='100%', directed=True, cdn_resources='remote')
    net.from_nx(G)
    
    # Style nodes
    for node in net.nodes:
        node_id = node['id']
        # Check if it's a domain node (has is_root property) or DNS record node
        if 'is_root' in G.nodes[node_id]:
            is_root = G.nodes[node_id]['is_root']
            node.update({
                'color': '#FF0000' if is_root else '#0000FF',
                'size': 30 if is_root else 20,
                'label': node_id
            })
        else:
            # It's a DNS record node
            status = G.nodes[node_id]['status']
            node.update({
                'color': '#00FF00',  # Different color for DNS records
                'size': 15,
                'label': f"{node_id}\n{status}"
            })
    
    return net

def visualize_domain_graph(graph_data):
    """Create an interactive visualization of the domain hierarchy."""
    G = _create_domain_graph(graph_data)
    net = _visualize_network(G)
    
    # Generate HTML file and display it
    filename = f'domain_graph_{datetime.now().strftime("%Y%m%d_%H%M%S")}.html'
    net.write_html(filename)
    display(HTML(filename))
    return filename

def add_dnsr_nodes(G, dnsr_graph_data):
    """Add DNS record nodes to the existing graph."""
    for dnsr_vertex, edge, domain_vertex in dnsr_graph_data:
        # Extract DNS record properties
        host = dnsr_vertex.properties['host']
        status = dnsr_vertex.properties['status_code']
        timestamp = dnsr_vertex.properties['timestamp']
        
        # Create a unique node ID for the DNS record
        dnsr_node_id = f"DNSR-{host}-{timestamp}"
        
        # Add new DNS record node
        G.add_node(dnsr_node_id, 
                   status=status,
                   host=host,
                   timestamp=timestamp)
        
        # Add edge from domain to its DNS record
        G.add_edge(host, dnsr_node_id)
    
    return G

def visualize_domain_and_dnsr_graph(domain_graph_data, dnsr_graph_data):
    G = _create_domain_graph(domain_graph_data)
    G = add_dnsr_nodes(G, dnsr_graph_data)
    net = _visualize_network(G)

    filename = f'domain_and_dnsr_graph_{datetime.now().strftime("%Y%m%d_%H%M%S")}.html'
    net.write_html(filename)
    display(HTML(filename))
    return filename

