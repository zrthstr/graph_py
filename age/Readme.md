Graph Database Project for IT Infrastructure Mapping

A tool to map and analyze IT infrastructure components including:
- Servers
- Domains and subdomains
- DNS records
- Networks and interfaces
- Virtual hosts
- Directories and web roots
- Load balancers
- CGI endpoints

Currently implemented using Apache AGE on PostgreSQL.

Data Collection:
The system ingests data from various security and network scanning tools including:
- subfinder
- dnsx
- nmap
- masscan
- dnsenum
- dnsrecon

Implementation:
Data from these tools is stored in a directory-based structure and processed
by this Python script using a ledger-style approach for consistent tracking
and historical records.
