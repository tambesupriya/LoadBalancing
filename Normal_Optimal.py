#!/usr/bin/env python
# coding: utf-8

# In[2]:


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
    
greedy_rem = capacity.copy()
random_rem = capacity.copy()
ran_avail = availableservices.copy()
edge_rem = capacity.copy()
ds_avail = availableservices.copy()

    
# Service Detailing
load = [];
for i in range(services):
    load.append(random.randint(1, 15));

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

#print("................................. Before Load Balancing .......................")

# Define model
mdl = Model(name="edge_cloud_optimization")

# Decision variables remain unchanged
x = mdl.binary_var_dict([(e, s) for e in range(edges) for s in range(services)], name="x")
y = mdl.binary_var_dict([(e, u) for e in range(edges) for u in range(users)], name="y")
z = mdl.binary_var_list(users, name="z")  # User allocation to cloud

# Objective: Maximize user requests served while balancing load
#beta = 0.1  # Weighting factor for load balance
#edge_utilization = [model.continuous_var(name=f"utilization_{e}") for e in range(edges)]

mdl.maximize(mdl.sum(y[e, u] for e in range(edges) for u in range(users)) - mdl.sum(x[e, s] for e in range(edges) for s in range(services)))

# Constraints
# Service availability
for e in range(edges):
    for u in range(users):
        mdl.add_constraint(y[e, u] <= x[e, demand[u] - 1], f"availability_{e}_{u}")

# Capacity constraints
for e in range(edges):
    mdl.add_constraint(mdl.sum(load[demand[u] - 1] * y[e, u] for u in range(users)) <= capacity[e], f"capacity_{e}")

# Proximity constraints
for e in range(edges):
    for u in range(users):
        mdl.add_constraint(randist[e][u] * y[e, u] <= coverage[e], f"proximity_{e}_{u}")

# 7. Server capacity constraints
for i in range(edges):
    mdl.add_constraint(mdl.sum(x[i, j] for j in range(services)) <= availableservices[i], f"service_capacity_{i}")

# At most one edge server or cloud per user
for u in range(users):
    mdl.add_constraint(mdl.sum(y[e, u] for e in range(edges)) + z[u] == 1, f"single_connection_{u}")

# Solve the model
solution = mdl.solve()
un = 0
us = 0

# Display results
# Output results
if solution:
        
    # Display total users served by edge and cloud
    users_served_by_edge = sum(solution.get_value(y[e, u]) for e in range(edges) for u in range(users))
    un = users_served_by_edge
    users_served_by_cloud = sum(solution.get_value(z[u]) for u in range(users))    
    services_deployed = sum(solution.get_value(x[e, s]) for e in range(edges) for s in range(services))
    us = services_deployed

    print(f"Users: {users_served_by_edge}")
    #print(f"Users served by Cloud: {users_served_by_cloud}")
    print(f"Services: {services_deployed}")
    end_time = time.time()
    execution_time = end_time - start_time
    print(f"Time: {execution_time:.2f}")
    
    # Calculate and display server utilization
    edge_utilize = [
        sum(load[demand[u] - 1] * solution.get_value(y[e, u]) for u in range(users)) / capacity[e] * 100
        for e in range(edges)]
    #print(f"Server Utilization (%): {edge_utilize}")

    # Calculate average server utilization variance
    if len(edge_utilize) > 1:
        avg_variance = statistics.variance(edge_utilize)
    else:
        avg_variance = 0  # If there's only one server, variance is not defined

    # Output results
    print("Variance: ", avg_variance)

else:
    print("No solution found.")

