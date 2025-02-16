"""
Visualization utilities for the domain graph data
"""

import networkx as nx
from pyvis.network import Network
from IPython.display import display, HTML

def visualize_domain_graph(graph_data):
    """
    Create an interactive visualization of the domain graph using Pyvis.
    
    Args:
        graph_data: List of tuples (root, relationship, domain) from dump_nodes_with_rel()
    
    Returns:
        IPython HTML display object with interactive graph
    """
    # Create a NetworkX graph
    G = nx.DiGraph()
    
    # Add nodes and edges from graph data
    for row in graph_data:
        root, rel, domain = row
        G.add_node(root.properties['host'], type='root')
        G.add_node(domain.properties['host'], type='subdomain')
        G.add_edge(root.properties['host'], domain.properties['host'])
    
    # Create interactive Pyvis network with remote CDN resources
    net = Network(notebook=True, height='500px', width='100%', 
                 directed=True, cdn_resources='remote')
    net.from_nx(G)
    
    # Style nodes based on type
    for node in net.nodes:
        if G.nodes[node['id']]['type'] == 'root':
            node['color'] = '#ff9999'  # Light red for root domains
        else:
            node['color'] = '#99ff99'  # Light green for subdomains
    
    # Show the graph
    net.show('domain_graph.html')
    return display(HTML('domain_graph.html'))

