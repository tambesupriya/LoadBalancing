#!/usr/bin/env python
# coding: utf-8

# In[1]:


from docplex.mp.model import Model
import operator
import pandas as pd
import random
import math
from operator import itemgetter
import statistics
import time


# Parameters
edges = 30  # Number of edge servers
users = 500  # Number of users
services = 3  # Number of services
max_variance = 0.3

num_edges = 125
num_users = 816

# To read edge server's location
df = pd.read_csv('edgecbd.csv', delimiter=',')
edgeloc = [list(row) for row in df.values]

dfu = pd.read_csv('usercbd.csv', delimiter=',')
userloc = [list(row) for row in dfu.values]

start_time = time.time()

coverage = []
capacity = []
availableservices = []
for i in range(edges):
    coverage.append(random.randint(250,400));
    capacity.append(random.randint(100,300));
    availableservices.append(random.randint(1, services));

# Service Detailing
load = [];
for i in range(services):
    load.append(random.randint(1, 15));
    
greedy_rem = capacity.copy()
random_rem = capacity.copy()
ran_avail = availableservices.copy()
edge_rem = capacity.copy()
ds_avail = availableservices.copy()


demand = [];
for i in range(users):
    demand.append(random.randint(1, services));
    
userArray = [];
a = random.sample(range(1, num_users+1), users);
for i in range(users):
    uloc = [];
    #t = random.randint(1, num_users-1);
    uloc.append(userloc[a[i-1]-1][0]);
    uloc.append(userloc[a[i-1]-1][1]);
    #uloc.append(userloc[t-1][1]);
    userArray.append(uloc);
#print(userArray)

edgeArray = [];
b = random.sample(range(1, num_edges+1), edges);
for i in range(edges):
    eloc = [];
    eloc.append(edgeloc[b[i-1]-1][0]);
    eloc.append(edgeloc[b[i-1]-1][1]);
    edgeArray.append(eloc);

randist = [];
R = 6371;
for e in range(edges):
    distloc = [];
    for u in range(users):
        dLat = (userArray[u][0]-edgeArray[e][0]) * (math.pi/180);
        dLon = (userArray[u][1]-edgeArray[e][1]) * (math.pi/180);
        a = math.sin(dLat/2) * math.sin(dLat/2) + math.cos((edgeArray[e][1])* (math.pi/180)) * math.cos((userArray[u][1])*(math.pi/180)) * math.sin(dLon/2) * math.sin(dLon/2); 
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a)); 
        d = R * c;
        distloc.append(d * 1000);
    randist.append(distloc);

rx = [[0 for i in range(services)] for j in range(edges)]
ry = [[0 for i in range(users)] for j in range(edges)]
#print("Print capacity: ", random_rem)
resourceutilization = 0
for u in range(users):  # User requests
    edge_cap = []
    for e in range(edges):  # Iterate through edge servers
        if randist[e][u] <= coverage[e]:  # Coverage constraint
            if rx[e][demand[u] - 1] == 1 and random_rem[e] - load[demand[u] - 1] > 0:
                edge_cap.append(e)
            elif rx[e][demand[u] - 1] == 0 and ran_avail[e] > 0:
                if random_rem[e] - load[demand[u] - 1] > 0:
                    edge_cap.append(e)
    
    if edge_cap:  # Allocate user to the best edge server
        #print("list:", edge_cap)
        random_element = random.choice(edge_cap)
        best_edge = random_element
        #print("Element:", best_edge)
        if rx[best_edge][demand[u] - 1] == 0:  # Deploy service if not already deployed
            rx[best_edge][demand[u] - 1] = 1
            ran_avail[best_edge] -= 1

        ry[best_edge][u] = 1  # Allocate user to edge server
        random_rem[best_edge] -= load[demand[u] - 1]
        resourceutilization += load[demand[u] - 1]

# Calculate server utilization as a one-dimensional list
random_server = [
    ((capacity[e] - random_rem[e]) / capacity[e]) * 100 if capacity[e] > 0 else 0
    for e in range(edges)
]

# Calculate average server utilization variance
if len(random_server) > 1:
    avg_variance = statistics.variance(random_server)
else:
    avg_variance = 0  # If there's only one server, variance is not defined

end_time = time.time()
execution_time = end_time - start_time
print("Time: ", execution_time)

# Output results
print("Variance: ", avg_variance)
print("Services: ", sum(sum(row) for row in rx))
print("Users: ", sum(sum(row) for row in ry))



# In[ ]:




