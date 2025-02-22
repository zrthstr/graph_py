import networkx as nx
from pyvis.network import Network
from IPython.display import HTML, display
from datetime import datetime

def _visualize_network(G, filename_prefix='domain_graph'):
    """Helper function to create an interactive visualization of a NetworkX graph."""
    net = Network(notebook=True, height='700px', width='100%', directed=True, cdn_resources='remote')
    net.from_nx(G)
    
    # Style nodes
    for node in net.nodes:
        is_root = G.nodes[node['id']]['is_root']
        node.update({
            'color': '#FF0000' if is_root else '#0000FF',
            'size': 30 if is_root else 20,
            'label': node['id']
        })
    
    # Generate HTML file and display it
    filename = f'{filename_prefix}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.html'
    net.write_html(filename)
    display(HTML(filename))
    return filename

def visualize_domain_graph(graph_data):
    """Create an interactive visualization of the domain hierarchy."""
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
    
    return _visualize_network(G)

def visualize_domain_and_dnsr_graph(graph_data):
    G = visualize_domain_graph(graph_data)
    return _visualize_network(G)

