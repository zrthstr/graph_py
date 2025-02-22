class DNSReccordNode:
    def __init__(self, host: str, status_code: int, a: list[str], aaaa: list[str], 
                 mx: list[str], ns: list[str], txt: list[str], cname: list[str], 
                 soa: list[str], ptr: list[str], spf: list[str], dkim: list[str], 
                 dmarc: list[str], timestamp: str):
        self.host = host
        self.status_code = status_code
        self.a = a
        self.aaaa = aaaa
        self.mx = mx
        self.ns = ns
        self.txt = txt
        self.cname = cname
        self.soa = soa
        self.ptr = ptr
        self.spf = spf
        self.dkim = dkim
        self.dmarc = dmarc
        self.timestamp = timestamp

    def __repr__(self):
        return (
            f"DNSReccordNode("
            f"host={self.host}, "
            f"status_code={self.status_code}, "
            f"a={self.a}, "
            f"aaaa={self.aaaa}, "
            f"mx={self.mx}, "
            f"ns={self.ns}, "
            f"txt={self.txt}, "
            f"cname={self.cname}, "
            f"soa={self.soa}, "
            f"ptr={self.ptr}, "
            f"spf={self.spf}, "
            f"dkim={self.dkim}, "
            f"dmarc={self.dmarc}, "
            f"timestamp={self.timestamp}, "
        )

