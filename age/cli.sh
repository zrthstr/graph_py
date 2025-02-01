psql postgresql://postgresUser:postgresPW@127.0.0.1:5455/postgresDB -c  'SET search_path TO ag_catalog; SELECT * FROM ag_graph; SELECT * FROM ag_label;'
