#!/usr/bin/env python
# coding: utf-8

# In[35]:


import random
import math
import pandas as pd
import statistics
import time

# Parameters
edges = 30  # Number of edge servers
users = 400  # Number of users
services = 9  # Multiple services (e.g., video, gaming, IoT, etc.)
R = 6371  # Earth radius in kilometers

# Load edge and user locations with improved error handling and structure validation
try:
    df = pd.read_csv('edgecbd.csv', delimiter=',')
    if df.empty:
        raise ValueError("edgecbd.csv is empty")
    if df.shape[1] < 2:
        raise ValueError("edgecbd.csv must have at least two columns (latitude, longitude)")
    edgeloc = df.values.tolist()  # Convert to list of rows

    dfu = pd.read_csv('usercbd.csv', delimiter=',')
    if dfu.empty:
        raise ValueError("usercbd.csv is empty")
    if dfu.shape[1] < 2:
        raise ValueError("usercbd.csv must have at least two columns (latitude, longitude)")
    userloc = dfu.values.tolist()  # Convert to list of rows

    #print(f"Loaded {len(edgeloc)} edge locations and {len(userloc)} user locations.")
except FileNotFoundError as e:
    print(f"Error: {e}. Please ensure edgecbd.csv and usercbd.csv are in the working directory.")
    exit(1)
except ValueError as e:
    print(f"Error: {e}. Check the CSV files for data and structure.")
    exit(1)
except Exception as e:
    print(f"Unexpected error loading CSV files: {e}")
    exit(1)

# Initialize random data with adjusted ranges
coverage = [random.randint(250, 400) for _ in range(edges)]  # Increased coverage radius in meters
capacity = [random.randint(100, 300) for _ in range(edges)]  # Increased server capacity
load = [random.randint(1, 15) for _ in range(services)]  # Load per service
demand = [random.randint(1, services) for _ in range(users)]  # Random service demand per user
max_services_per_edge = [random.randint(1, services) for _ in range(edges)]  # Increased minimum services per edge

# Randomly select user and edge locations
userArray = []
a = random.sample(range(len(userloc)), users)  # Sample from available user locations
for i in range(users):
    uloc = [userloc[a[i]][0], userloc[a[i]][1]]  # Access latitude and longitude
    userArray.append(uloc)

edgeArray = []
b = random.sample(range(len(edgeloc)), edges)  # Sample from available edge locations
for i in range(edges):
    eloc = [edgeloc[b[i]][0], edgeloc[b[i]][1]]  # Access latitude and longitude
    edgeArray.append(eloc)

# Calculate distances
randist = []
for e in range(edges):
    distloc = []
    for u in range(users):
        dLat = (userArray[u][0] - edgeArray[e][0]) * (math.pi / 180)
        dLon = (userArray[u][1] - edgeArray[e][1]) * (math.pi / 180)
        a = math.sin(dLat / 2) * math.sin(dLat / 2) + math.cos(edgeArray[e][1] * (math.pi / 180)) * math.cos(userArray[u][1] * (math.pi / 180)) * math.sin(dLon / 2) * math.sin(dLon / 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        d = R * c * 1000  # Distance in meters
        distloc.append(d)
    randist.append(distloc)

# Binary PSO Implementation
class BinaryPSO:
    def __init__(self, num_particles, max_iter, edges, users, capacity, load, randist, coverage, max_services_per_edge, services, max_util_diff):
        self.num_particles = num_particles
        self.max_iter = max_iter
        self.edges = edges
        self.users = users
        self.services = services
        self.capacity = capacity
        self.load = load
        self.randist = randist
        self.coverage = coverage
        self.max_services_per_edge = max_services_per_edge
        self.max_util_diff = max_util_diff  # Maximum allowable utilization difference (e.g., 20 for 0.2)
        self.w = 0.7  # Inertia weight
        self.c1 = 2.0  # Cognitive coefficient
        self.c2 = 2.0  # Social coefficient
        self.particles = []
        self.pBest = []
        self.pBest_fitness = [float('inf')] * num_particles
        self.gBest = {'deployment': [[0 for _ in range(services)] for _ in range(edges)], 'allocation': [0] * users}
        self.gBest_fitness = float('inf')
        self.utilization = [0] * edges
        self.initialize_particles()

    def initialize_particles(self):
        for i in range(self.num_particles):
            deployment = []
            for e in range(self.edges):
                row = [0] * services
                num_services_to_deploy = random.randint(1, self.max_services_per_edge[e])
                service_indices = random.sample(range(self.services), num_services_to_deploy)
                for s in service_indices:
                    row[s] = 1
                deployment.append(row)

            allocation = [-1] * self.users
            temp_utilization = [0] * self.edges
            for u in range(self.users):
                best_edge = -1
                min_utilization = float('inf')
                for s in range(self.services):
                    valid_edges = [(e, temp_utilization[e]) for e in range(self.edges) if deployment[e][s] == 1 and self.randist[e][u] <= self.coverage[e] and temp_utilization[e] + self.load[s] <= self.capacity[e]]
                    if valid_edges:
                        valid_edges.sort(key=lambda x: x[1])
                        chosen_edge, edge_utilization = valid_edges[0]
                        if edge_utilization < min_utilization:
                            min_utilization = edge_utilization
                            best_edge = chosen_edge
                if best_edge >= 0:
                    allocation[u] = best_edge
                    temp_utilization[best_edge] += self.load[demand[u]-1]

            velocity = [random.uniform(-1, 1) for _ in range(self.edges * self.services + self.users)]
            self.particles.append({'deployment': deployment, 'allocation': allocation, 'velocity': velocity})
            fitness = self.fitness(deployment, allocation)
            if fitness < self.pBest_fitness[i]:
                self.pBest.append({'deployment': [row[:] for row in deployment], 'allocation': allocation.copy()})
                self.pBest_fitness[i] = fitness
            if fitness < self.gBest_fitness:
                self.gBest['deployment'] = [row[:] for row in deployment]
                self.gBest['allocation'] = allocation.copy()
                self.gBest_fitness = fitness
                self.update_utilization(allocation, deployment)

    def fitness(self, deployment, allocation):
        utilization = [0] * self.edges
        users_served = 0
        total_deployments = sum(sum(1 for s in range(self.services) if deployment[e][s]) for e in range(self.edges))

        for u in range(self.users):
            e = allocation[u]
            if e >= 0 and deployment[e][demand[u]-1] == 1 and self.randist[e][u] <= self.coverage[e] and utilization[e] + self.load[demand[u]-1] <= self.capacity[e]:
                utilization[e] += self.load[demand[u]-1]
                users_served += 1

        # Calculate maximum utilization difference
        if any(u > 0 for u in utilization):
            max_diff = max(max(utilization) - min(u for u in utilization if u > 0), 0)  # Avoid division by zero
        else:
            max_diff = 0

        # Base fitness
        fitness = 0.5 * max_diff + 0.3 * total_deployments - 0.5 * users_served
        # Capacity penalty
        penalty = 0
        for e in range(self.edges):
            if utilization[e] > self.capacity[e]:
                penalty += (utilization[e] - self.capacity[e]) * 100
        fitness += penalty
        # Utilization difference penalty if it exceeds the maximum allowable
        if max_diff > self.max_util_diff:
            util_diff_penalty = (max_diff - self.max_util_diff) * 1000  # Heavy penalty to enforce constraint
            fitness += util_diff_penalty

        return fitness

    def update_utilization(self, allocation, deployment):
        self.utilization = [0] * self.edges
        for u in range(self.users):
            e = allocation[u]
            if e >= 0 and deployment[e][demand[u]-1] == 1 and self.randist[e][u] <= self.coverage[e] and self.utilization[e] + self.load[demand[u]-1] <= self.capacity[e]:
                self.utilization[e] += self.load[demand[u]-1]

    def update_velocity_position(self):
        for i in range(self.num_particles):
            temp_utilization = [0] * self.edges
            for u in range(self.users):
                e = self.particles[i]['allocation'][u]
                if e >= 0 and self.particles[i]['deployment'][e][demand[u]-1] == 1 and self.randist[e][u] <= self.coverage[e] and temp_utilization[e] + self.load[demand[u]-1] <= self.capacity[e]:
                    temp_utilization[e] += self.load[demand[u]-1]

            for j in range(self.edges * self.services + self.users):
                r1, r2 = random.random(), random.random()
                if j < self.edges * self.services:
                    e = j // self.services
                    s = j % self.services
                    pBest_d = self.pBest[i]['deployment'][e][s] if self.pBest[i]['deployment'][e][s] >= 0 else 0
                    gBest_d = self.gBest['deployment'][e][s] if self.gBest['deployment'][e][s] >= 0 else 0
                    current_services = sum(self.particles[i]['deployment'][e])
                    self.particles[i]['velocity'][j] = (self.w * self.particles[i]['velocity'][j] +
                                                      self.c1 * r1 * (pBest_d - self.particles[i]['deployment'][e][s]) +
                                                      self.c2 * r2 * (gBest_d - self.particles[i]['deployment'][e][s]))
                    if self.particles[i]['velocity'][j] > 6:
                        self.particles[i]['velocity'][j] = 6
                    elif self.particles[i]['velocity'][j] < -6:
                        self.particles[i]['velocity'][j] = -6
                    probability = 1 / (1 + math.exp(-self.particles[i]['velocity'][j]))
                    if current_services < self.max_services_per_edge[e] and random.random() < probability:
                        self.particles[i]['deployment'][e][s] = 1
                    else:
                        self.particles[i]['deployment'][e][s] = 0
                else:
                    u = j - self.edges * self.services
                    pBest_e = self.pBest[i]['allocation'][u] if self.pBest[i]['allocation'][u] >= 0 else 0
                    gBest_e = self.gBest['allocation'][u] if self.gBest['allocation'][u] >= 0 else 0
                    self.particles[i]['velocity'][j] = (self.w * self.particles[i]['velocity'][j] +
                                                      self.c1 * r1 * (pBest_e - self.particles[i]['allocation'][u]) +
                                                      self.c2 * r2 * (gBest_e - self.particles[i]['allocation'][u]))
                    if self.particles[i]['velocity'][j] > 6:
                        self.particles[i]['velocity'][j] = 6
                    elif self.particles[i]['velocity'][j] < -6:
                        self.particles[i]['velocity'][j] = -6
                    probability = 1 / (1 + math.exp(-self.particles[i]['velocity'][j]))
                    best_edge = -1
                    min_utilization = float('inf')
                    for s in range(self.services):
                        valid_edges = [(e, temp_utilization[e]) for e in range(self.edges) if self.particles[i]['deployment'][e][s] == 1 and self.randist[e][u] <= self.coverage[e] and temp_utilization[e] + self.load[s] <= self.capacity[e]]
                        if valid_edges:
                            valid_edges.sort(key=lambda x: x[1])
                            chosen_edge, edge_utilization = valid_edges[0]
                            if edge_utilization < min_utilization:
                                min_utilization = edge_utilization
                                best_edge = chosen_edge
                    if best_edge >= 0 and random.random() < probability:
                        old_edge = self.particles[i]['allocation'][u]
                        self.particles[i]['allocation'][u] = best_edge
                        if old_edge >= 0 and self.particles[i]['deployment'][old_edge][demand[u]-1] == 1 and self.randist[old_edge][u] <= self.coverage[old_edge]:
                            temp_utilization[old_edge] = max(0, temp_utilization[old_edge] - self.load[demand[u]-1])
                        new_edge = self.particles[i]['allocation'][u]
                        if new_edge >= 0 and self.particles[i]['deployment'][new_edge][demand[u]-1] == 1 and self.randist[new_edge][u] <= self.coverage[new_edge] and temp_utilization[new_edge] + self.load[demand[u]-1] <= self.capacity[new_edge]:
                            temp_utilization[new_edge] += self.load[demand[u]-1]
                    else:
                        self.particles[i]['allocation'][u] = -1

    def optimize(self):
        for _ in range(self.max_iter):
            for i in range(self.num_particles):
                fitness = self.fitness(self.particles[i]['deployment'], self.particles[i]['allocation'])
                if fitness < self.pBest_fitness[i]:
                    self.pBest[i] = {'deployment': [row[:] for row in self.particles[i]['deployment']], 'allocation': self.particles[i]['allocation'].copy()}
                    self.pBest_fitness[i] = fitness
                if fitness < self.gBest_fitness:
                    self.gBest['deployment'] = [row[:] for row in self.particles[i]['deployment']]
                    self.gBest['allocation'] = self.particles[i]['allocation'].copy()
                    self.gBest_fitness = fitness
                    self.update_utilization(self.gBest['allocation'], self.gBest['deployment'])
            self.update_velocity_position()
        return self.gBest, self.gBest_fitness

# Set single values for max_util_diff and max_iter
max_util_diff = 30  # Example value (corresponding to 0.2), change to 30, 60, or 70 as needed
num_particles = 35
max_iter = 120

# Initialize and run PSO with the single max_util_diff
pso = BinaryPSO(num_particles, max_iter, edges, users, capacity, load, randist, coverage, max_services_per_edge, services, max_util_diff)

# Measure the time taken for optimization
start_time = time.time()
best_solution, best_fitness = pso.optimize()
end_time = time.time()
execution_time = end_time - start_time

# Output results
users_served = sum(1 for u in range(users) if best_solution['allocation'][u] >= 0)
utilization = [0] * edges
deployment = best_solution['deployment']
for u in range(users):
    e = best_solution['allocation'][u]
    if e >= 0 and deployment[e][demand[u]-1] == 1 and randist[e][u] <= coverage[e] and utilization[e] + load[demand[u]-1] <= capacity[e]:
        utilization[e] += load[demand[u]-1]

total_services_deployed = sum(sum(1 for s in range(services) if deployment[e][s]) for e in range(edges))
if len(utilization) > 1 and any(u > 0 for u in utilization):
    max_diff = max(max(utilization) - min(u for u in utilization if u > 0), 0)
    variance = statistics.variance(utilization)
    average_variance = variance / edges
else:
    max_diff = 0
    average_variance = 0

#print(f"Max Utilization Difference Threshold: {max_util_diff}")
print(f"Services: {total_services_deployed}")
print(f"Users: {users_served}")
#print(f"Max Utilization Difference: {max_diff}")
print(f"Variance: {average_variance * 100}")
print(f"Time: {execution_time:.2f}")


