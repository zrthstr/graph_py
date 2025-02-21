class DomainNode:
    def __init__(self, host, _input, source, is_implicit=False, is_root=False):
        self.host = host
        self.input = _input
        self.source = source
        self.is_implicit = is_implicit
        self.is_root = False

    def get_implicit_nodes(self):
        parts = self.host.split('.')
        root_parts = self.input.split('.')
        subdomain_parts = parts[:-len(root_parts)] + [".".join(root_parts)]

        return [
            DomainNode(".".join(subdomain_parts[i:]), self.input, "implicit")
            for i in range(len(subdomain_parts))
        ]

    def get_node_DB_status(self):
        pass
        
    @classmethod
    def from_age_vertex(cls, vertex, root_domain=None):
        host = vertex.properties['host']
        source = vertex.properties.get('source', 'unknown')
        _input = root_domain if root_domain else host
        is_root = vertex.properties.get('is_root', False)
        is_implicit = vertex.properties.get('is_implicit', False)
        return cls(host=host, _input=_input, source=source, is_implicit=is_implicit, is_root=is_root)

    def __repr__(self):
        return (
            f"DomainNode("
            f"host={self.host}, "
            f"input={self.input}, "
            f"source={self.source}, "
            f"is_implicit={self.is_implicit}, "
            f"is_root={self.is_root})"
        ) 