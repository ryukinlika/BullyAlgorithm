from flask import Flask, request, jsonify
from util_methods import register_service, get_ports_of_nodes, generate_node_id, get_higher_nodes, election, \
    announce, ready_for_election, get_details, check_health_of_the_service, get_single_detail
from bully import Bully
import threading
import time
import random
import sys
import requests
from multiprocessing import Value
import logging


counter = Value('i', 0)
app = Flask(__name__)

# verifying if port number and node name have been entered as command line arguments.
port_number = int(sys.argv[1])
assert port_number

node_name = sys.argv[2]
assert node_name

# saving the API logs to a file
logging.basicConfig(filename=f"logs/{node_name}.log", level=logging.INFO)


# node_id = generate_node_id()
node_id = port_number
bully = Bully(node_name, node_id, port_number)

# register service in the Consul Service Registry
service_register_status = register_service(node_name, port_number, node_id)

# global iteration count
roundCount = -1

def init(wait=True, iteration=0):
    if service_register_status == 200:
        global roundCount
        ports_of_all_nodes = get_ports_of_nodes()
        del ports_of_all_nodes[node_name]
        if roundCount < iteration: 
            roundCount = iteration
            print("############# [[Election #%s]]  ################" %roundCount)

        do_elections(ports_of_all_nodes, wait, roundCount)
    else:
        print('Service registration is not successful')


def do_elections(ports_of_all_nodes, wait=True, iteration=0): 
    global bully
    if wait:
        timeout = random.randint(5, 10)
        time.sleep(timeout)
        print('[[Election#%s]] timeouting in %s seconds' % (iteration,timeout))

    # checks if there is an election on going
    election_ready, node_details = ready_for_election(ports_of_all_nodes, bully.election, bully.coordinator)
    if election_ready or not wait:
        print('Starting election#%s in: %s' % (iteration, node_name))
        bully.election = True
        higher_nodes_array = get_higher_nodes(node_details, node_id)
        print("[[Election#%s]]"% iteration)
        print('higher node array', higher_nodes_array)
        if len(higher_nodes_array) == 0:
            bully.coordinator = True
            bully.coorPort = port_number
            bully.election = False
            announce(node_name, port_number)
            print('**********Coordinator#%s Elected***********' %iteration)
            print('[[Election#%s]]Coordinator is : %s' % (iteration, node_name))
        else:
            election(higher_nodes_array, node_id)




# this api is used to exchange details with each node
@app.route('/nodeDetails', methods=['GET'])
def get_node_details():
    coordinator_bully = bully.coordinator
    node_id_bully = bully.node_id
    election_bully = bully.election
    node_name_bully = bully.node_name
    port_number_bully = bully.port
    return jsonify({'node_name': node_name_bully, 'node_id': node_id_bully, 'coordinator': coordinator_bully,
                    'election': election_bully, 'port': port_number_bully, 'coorPort': bully.coorPort}), 200


'''
This API checks if the incoming node ID is grater than its own ID. If it is, it executes the init method and 
sends an OK message to the sender. The execution is handed over to the current node. 
'''
@app.route('/response', methods=['POST'])
def response_node():
    data = request.get_json()
    incoming_node_id = data['node_id']
    self_node_id = bully.node_id
    if self_node_id > incoming_node_id:
        threading.Thread(target=init, args=[False]).start()
        bully.election = False
    return jsonify({'Response': 'OK'}), 200


# This API is used to announce the coordinator details.
@app.route('/announce', methods=['POST'])
def announce_coordinator():
    data = request.get_json()
    coordinator = data['coordinator']
    coorPort = data['coorPort']
    bully.coordinator = coordinator
    bully.coorPort = coorPort
    print('Coordinator is %s ' % coordinator)
    return jsonify({'response': 'OK'}), 200


'''
When nodes are sending the election message to the higher nodes, all the requests comes to this proxy. As the init
method needs to execute only once, it will forward exactly one request to the responseAPI. 
'''
@app.route('/proxy', methods=['POST'])
def proxy():
    with counter.get_lock():
        counter.value += 1
        unique_count = counter.value

    url = 'http://localhost:%s/response' % port_number
    if unique_count == 1:
        data = request.get_json()
        requests.post(url, json=data)


    return jsonify({'Response': 'OK'}), 200


# No node spends idle time, they always checks if the master node is alive in each 60 seconds.
# def check_coordinator_health():
#     threading.Timer(60.0, check_coordinator_health).start()
#     health = check_health_of_the_service(bully.coordinator)
#     if health == 'crashed':
#         init()
#     else:
#         print('Coordinator is alive')

def check_coordinator_alive():
    global bully
    if bully.coorPort == port_number: 
        print("self is coordinator")
    elif bully.coorPort == 0: 
        print("not initialized")
    else: 
        status = get_single_detail(bully.coorPort)
        if status == False: # coor dead
            print("Coordinator %s crashed" % bully.coorPort)
            bully.election = False
            bully.coordinator = False
            bully.coorPort = 0
            with counter.get_lock(): # so response is only once 
                counter.value = 0
            init(True, roundCount+1)
        else: 
            print("coordinator %s is alive" %bully.coorPort)
            
    new_timer = threading.Timer(30, check_coordinator_alive)
    new_timer.start()

timer_thread1 = threading.Timer(5, init, kwargs={"iteration":0}) #do init after 5 seconds
timer_thread1.start()

timer_thread2 = threading.Timer(40, check_coordinator_alive)
timer_thread2.start() 


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=port_number)