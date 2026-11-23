#!/usr/bin/env python
# coding: utf-8

# In[17]:


#!/usr/bin/env python
# coding: utf-8

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
users = 400  # Number of users
services = 9 # Number of services
max_variance = 30
itr = 0
num_edges = 125
num_users = 816

# To read edge server's location
df = pd.read_csv('edgecbd.csv', delimiter = ',')
edgeloc = [list(row) for row in df.values]

dfu = pd.read_csv('usercbd.csv', delimiter = ',')
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
    
def calculate_utilization_variance():
    """Calculate variance of utilization across all edge servers."""
    utilizations = [
        (capacity[e] - edge_rem[e]) / capacity[e] if capacity[e] > 0 else 0
        for e in range(edges)
    ]
    return statistics.variance(utilizations) if len(utilizations) > 1 else 0

def calculate_score_with_variance(utilization, remaining_capacity, service_count, projected_variance):
    """Calculate the score for an edge considering utilization variance."""
    return (
        utilization + remaining_capacity + service_count - projected_variance
    )

# Initialize coverage data structures
usercovered = [[] for _ in range(users)]
edgecovered = [[] for _ in range(edges)]

for u in range(users):
    for e in range(edges):
        if randist[e][u] <= coverage[e]:
            usercovered[u].append(e)
            edgecovered[e].append(u)

sorted_usercovered = sorted(
    enumerate(usercovered),
    key=lambda x: len(x[1]),
    reverse=False
)

sorted_indices = [item[0] for item in sorted_usercovered]
sorted_usercovered = [item[1] for item in sorted_usercovered]

edgecovered_service_count = []
for e in range(edges):
    service_count = {s: 0 for s in range(1, services + 1)}
    for u in edgecovered[e]:
        service_count[demand[u]] += 1
    edgecovered_service_count.append(service_count)

clouduser = []
ds = [[0 for _ in range(services)] for _ in range(edges)]
du = [[0 for _ in range(users)] for _ in range(edges)]

def calculate_utilization(edge_id):
    """Calculate the utilization of a given edge server."""
    return (capacity[edge_id] - edge_rem[edge_id]) / capacity[edge_id] if capacity[edge_id] > 0 else 0

for u in sorted_indices:
    # covered by no server
    if len(sorted_usercovered[u]) < 1:
        clouduser.append(sorted_indices[u])
    # covered by one server
    elif len(sorted_usercovered[u]) == 1:
        ed = sorted_usercovered[u][0]
        if ds[ed][demand[sorted_indices[u]] - 1] == 1 and edge_rem[ed] >= load[demand[sorted_indices[u]] - 1]:
            du[ed][sorted_indices[u]] = 1
            edge_rem[ed] -= load[demand[sorted_indices[u]] - 1]
            edgecovered = [[item for item in row if item != sorted_indices[u]] for row in edgecovered]
        elif ds_avail[ed] > 0 and edge_rem[ed] >= load[demand[sorted_indices[u]] - 1]:
            ds[ed][demand[sorted_indices[u]] - 1] = 1
            ds_avail[ed] -= 1
            du[ed][sorted_indices[u]] = 1
            edge_rem[ed] -= load[demand[sorted_indices[u]] - 1]
            edgecovered = [[item for item in row if item != sorted_indices[u]] for row in edgecovered]
        else:
            clouduser.append(sorted_indices[u])
    else:
        edge_details = []
        for ed in sorted_usercovered[u]:
            if ds[ed][demand[sorted_indices[u]] - 1] == 1 and edge_rem[ed] - load[demand[sorted_indices[u]] - 1] > 0:
                # Simulate allocation to this edge
                temp_edge_rem = edge_rem[ed] - load[demand[sorted_indices[u]] - 1]
                temp_utilizations = [
                    (capacity[e] - (temp_edge_rem if e == ed else edge_rem[e])) / capacity[e] if capacity[e] > 0 else 0
                    for e in range(edges)
                ]
                projected_variance = statistics.variance(temp_utilizations) if len(temp_utilizations) > 1 else 0

                edge_details.append({
                    "edge": ed,
                    "score": calculate_score_with_variance(
                        calculate_utilization(ed),
                        edge_rem[ed],
                        edgecovered_service_count[ed].get(demand[sorted_indices[u]] - 1, 0),
                        projected_variance
                    ),
                    "projected_variance": projected_variance
                })
        if edge_details:
            first_edge = sorted(edge_details, key=lambda x: (x["score"]), reverse=False)[0]["edge"]
            #first_edge = sorted(edge_details, key=lambda x: (x["score"]), reverse=True)[0]["edge"]
            du[first_edge][sorted_indices[u]] = 1
            edge_rem[first_edge] -= load[demand[sorted_indices[u]] - 1]
            edgecovered = [[item for item in row if item != sorted_indices[u]] for row in edgecovered]
        else:
            for ed in sorted_usercovered[u]:
                if ds_avail[ed] > 0 and edge_rem[ed] - load[demand[sorted_indices[u]] - 1] > 0:
                    temp_edge_rem = edge_rem[ed] - load[demand[sorted_indices[u]] - 1]
                    temp_utilizations = [
                        (capacity[e] - (temp_edge_rem if e == ed else edge_rem[e])) / capacity[e] if capacity[e] > 0 else 0
                    for e in range(edges)
                    ]
                    projected_variance = statistics.variance(temp_utilizations) if len(temp_utilizations) > 1 else 0

                    edge_details.append({
                        "edge": ed,
                        "score": calculate_score_with_variance(
                            calculate_utilization(ed),
                            edge_rem[ed],
                            edgecovered_service_count[ed].get(demand[sorted_indices[u]] - 1, 0),
                            projected_variance
                        ),
                        "capacity": edge_rem[ed],
                        "available_services": ds_avail[ed],
                        "projected_variance": projected_variance
                    })
                    
            if edge_details:
                #first_edge = sorted(
                #    edge_details,
                #    key=lambda x: (x["utilization"], x["capacity"], x["available_services"], x["user_service_count"]),
                #    reverse=True)[0]["edge"]
                first_edge = sorted(edge_details, key=lambda x: (x["capacity"], x["available_services"]), reverse=False)[0]["edge"]
                #first_edge = sorted(
                #    edge_details,
                #    key=lambda x: (x["score"]),
                #    reverse=False)[0]["edge"]
                ds[first_edge][demand[sorted_indices[u]] - 1] = 1
                ds_avail[first_edge] -= 1
                du[first_edge][sorted_indices[u]] = 1
                edge_rem[first_edge] -= load[demand[sorted_indices[u]] - 1]
                edgecovered = [[item for item in row if item != sorted_indices[u]] for row in edgecovered]
            else:
                clouduser.append(sorted_indices[u])
                
# Calculate server utilization as a one-dimensional list
greedy_server = [
    ((capacity[e] - edge_rem[e]) / capacity[e]) * 100 if capacity[e] > 0 else 0
    for e in range(edges)
]

# Calculate average server utilization variance
if len(greedy_server) > 1:
    avg_variance = statistics.variance(greedy_server)
else:
    avg_variance = 0  # If there's only one server, variance is not defined

# Output results
#print("Average Server Utilization Variance:", avg_variance)
#print("Services: ", sum(sum(row) for row in ds))
#print("Users: ", sum(sum(row) for row in du))

def updated_greedy_load_balancing(edges, users, du, edge_rem, capacity, demand, load, 
                                  usercovered, edgecovered, ds, ds_avail, max_variance, convergence_threshold=1e-6):
    """Updated greedy heuristic for load balancing with minimal service deployments.
    Runs until utilization variance stabilizes (no significant improvement)."""
    prev_variance = float('inf')  # Initialize with a high value

    while True:
        global itr 
        itr = itr + 1
        # Calculate current utilization metrics
        utilizations = [(1 - (rem / cap)) * 100 if cap > 0 else 0 for rem, cap in zip(edge_rem, capacity)]
        avg_util = sum(utilizations) / len(utilizations) if utilizations else 0
        current_variance = statistics.variance(utilizations) if len(utilizations) > 1 else 0

        # Check for convergence
        if abs(prev_variance - current_variance) < convergence_threshold:
            break  # Stop if variance improvement is negligible
        prev_variance = current_variance

        # Identify candidate servers
        over_utilized = [e for e, util in enumerate(utilizations) if util > avg_util + max_variance]
        under_utilized = [e for e, util in enumerate(utilizations) if util < avg_util - max_variance]

        if not over_utilized or not under_utilized:
            break  # Stop if no servers need adjustment

        # Rebalance users from over-utilized to under-utilized servers
        for hv in over_utilized:
            assigned_users = [u for u in range(users) if du[hv][u] == 1]
            for user in assigned_users:
                service_type = demand[user] - 1  # 0-based index
                required_load = load[service_type]

                # Find viable target servers in user's coverage
                viable_targets = [
                    lv for lv in under_utilized
                    if lv in usercovered[user]
                    and edge_rem[lv] >= required_load
                ]

                # Split targets by service availability
                existing_service_targets = [lv for lv in viable_targets if ds[lv][service_type] == 1]
                deployable_targets = [
                    lv for lv in viable_targets
                    if ds[lv][service_type] == 0
                    and ds_avail[lv] > 0
                ]

                # Prioritize targets with existing service
                for lv in existing_service_targets + deployable_targets:
                    if ds[lv][service_type] == 0:
                        # Deploy service if needed and possible
                        ds[lv][service_type] = 1
                        ds_avail[lv] -= 1

                    # Reallocate user
                    du[hv][user] = 0
                    edge_rem[hv] += required_load
                    du[lv][user] = 1
                    edge_rem[lv] -= required_load

                    # Recalculate utilizations after reallocation
                    utilizations = [(1 - (rem / cap)) * 100 if cap > 0 else 0 for rem, cap in zip(edge_rem, capacity)]
                    current_variance = statistics.variance(utilizations) if len(utilizations) > 1 else 0

                    # If variance improves, keep the reallocation; otherwise, revert
                    if current_variance < prev_variance:
                        break  # Keep the reallocation and move to the next user
                    else:
                        # Revert reallocation
                        du[hv][user] = 1
                        edge_rem[hv] -= required_load
                        du[lv][user] = 0
                        edge_rem[lv] += required_load
                        if ds[lv][service_type] == 1 and lv in deployable_targets:
                            ds[lv][service_type] = 0
                            ds_avail[lv] += 1
                else:
                    continue  # No viable target found for this user
                break  # Move to the next user after successful reallocation

    # Calculate final metrics
    final_util = [(1 - (rem / cap)) * 100 if cap > 0 else 0 for rem, cap in zip(edge_rem, capacity)]
    return final_util, statistics.variance(final_util) if len(final_util) > 1 else 0

# Apply the updated greedy load balancing
ds_utilization, final_variance = updated_greedy_load_balancing(
    edges, users, du, edge_rem, capacity, demand, load, usercovered, edgecovered, ds, ds_avail, max_variance)

# Output results
print("Final Metrics After Greedy Load Balancing")
print("Services: ", sum(sum(row) for row in ds))
print("Users: ", sum(sum(row) for row in du))
print("Variance: ", final_variance)
print("Iteration: ", itr)
end_time = time.time()
execution_time = end_time - start_time
print("Time: ", execution_time)

