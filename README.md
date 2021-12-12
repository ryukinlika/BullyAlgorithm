# Bully Algorithm Implementation
## HEAVILY BASED ON https://github.com/isuruuy429/Masters/tree/master/BullyAlgorithm
Full credit belongs to the original code creator 
Code was modified to support a scenario where coordinator in a cluster crashed, and added some logs and error-handling function

# Setup 
1. Install Consul (https://www.consul.io/)
2. Verify that Consul has successfully been installed by using 
```
consul --version 
```
3. Start the Consul agetn 
```
consul agent -dev 
```
4. For this example, the cluster has 4 nodes with the same code base. These codes need to be run in a different terminal. Port number and node name must be provided via command line arguments. In this scenario, the bully algorithm takes the node with the highest port number as the coordinator of a cluster.  
Node 1
```
py new.py 5001 node1
```
Node 2
```
py new2.py 5002 node1
```
Node 3
```
py new3.py 5003 node1
```
Node 4
```
py new4.py 5004 node1
```

Coordinator node output: 
```
 * Serving Flask app 'new4' (lazy loading)
 * Environment: production
   WARNING: This is a development server. Do not use it in a production deployment.   
   Use a production WSGI server instead.   
 * Debug mode: off
############# [[Election #0]]  ################
[[Election#0]] timeouting in 5 seconds
Starting election#0 in: node4
[[Election#0]]
higher node array []
http://localhost:5002/announce
http://localhost:5004/announce
Coordinator is node4 
http://localhost:5003/announce
http://localhost:5001/announce
**********Coordinator#0 Elected***********
[[Election#0]]Coordinator is : node4
Starting election#0 in: node4
[[Election#0]]
higher node array []
http://localhost:5002/announce
http://localhost:5004/announce
Coordinator is node4 
http://localhost:5003/announce
http://localhost:5001/announce
**********Coordinator#0 Elected***********
[[Election#0]]Coordinator is : node4
self is coordinator
```

Non-coordinator node output: 
```
 * Serving Flask app 'new3' (lazy loading)
 * Environment: production
   WARNING: This is a development server. Do not use it in a production deployment.     
   Use a production WSGI server instead.    
 * Debug mode: off
############# [[Election #0]]  ################
[[Election#0]] timeouting in 5 seconds
Starting election#0 in: node3
[[Election#0]]
higher node array [5004]
Coordinator is node4 
Coordinator is node4 
coordinator 5004 is alive
error connecting node 5004
Coordinator 5004 crashed
############# [[Election #1]]  ################
[[Election#1]] timeouting in 9 seconds
error connecting node 5004
error connecting node 5004
Starting election#1 in: node3
[[Election#1]]
higher node array []
http://localhost:5002/announce
http://localhost:5004/announce
error annoucing to node 5004
http://localhost:5003/announce
Coordinator is node3 
http://localhost:5001/announce
**********Coordinator#1 Elected***********
[[Election#1]]Coordinator is : node3
```

