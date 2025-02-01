
apple = "apple.sqlite"
from simple_graph_sqlite import database as db

db.initialize(apple)
db.atomic(apple, db.add_node({'name': 'Apple Computer Company', 'type':['company', 'start-up'], 'founded': 'April 1, 1976'}, 1))

db.atomic(apple, db.add_node({'name': 'Steve Wozniak', 'type':['person','engineer','founder']}, 2))

db.atomic(apple, db.connect_nodes(2, 1, {'action': 'founded'}))

db.atomic(apple, db.find_node(1))
