"""
Visualization utilities for the domain graph data
"""

import networkx as nx
from pyvis.network import Network
from IPython.display import display, HTML
from datetime import datetime
import os

def visualize_domain_graph(graph_data):
    """Create an interactive visualization of the domain hierarchy."""
    G = nx.DiGraph()
    
    for root, rels, sub in graph_data:
        # Add nodes and edges exactly as they are in the database
        G.add_node(root.host, type='root')
        G.add_node(sub.host, type='domain', source=sub.source)
        G.add_edge(root.host, sub.host)
    
    net = Network(height='700px', width='100%', directed=True)
    net.from_nx(G)
    
    for node in net.nodes:
        is_root = G.nodes[node['id']]['type'] == 'root'
        node.update({
            'color': '#FF0000' if is_root else '#0000FF',
            'size': 30 if is_root else 20,
            'label': node['id']
        })
    
    filename = f'domain_graph_{datetime.now().strftime("%Y%m%d_%H%M%S")}.html'
    try:
        net.show(filename)
        display(HTML(filename))
        return filename
    finally:
        net.clear()

