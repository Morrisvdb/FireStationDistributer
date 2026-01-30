import osmnx as ox
import networkx as nx
import json
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed
import os

# -----------------------------
# CONFIG
# -----------------------------
PLACE_NAME = "Brooklyn, New York, USA"

MAX_RESPONSE_TIME_MIN = 6

place_stripped = PLACE_NAME.split(",")[0].lower()
OUTPUT_FILE = place_stripped+"_firestation_solution.json"

MAX_RESPONSE_TIME_SEC = MAX_RESPONSE_TIME_MIN * 60
SPEED_INCREASE_KPH = 20


# -----------------------------
# LOAD GRAPH
# -----------------------------
print("Loading road network...")
G = ox.graph_from_place(
    PLACE_NAME,
    network_type="drive",
    simplify=True
)

# -----------------------------
# ADD TRAVEL TIME
# -----------------------------
print("Adding travel times...")
G = ox.add_edge_speeds(G)

# Add SPEED_INCREASE_KPH to all the speed limits
for u, v, k, data in G.edges(keys=True, data=True):
    base_speed = data.get("speed_kph", 0.0)
    new_speed = base_speed + SPEED_INCREASE_KPH
    data["speed_kph"] = max(new_speed, 0.1)

for u, v, k, data in G.edges(keys=True, data=True):
    length_m = data.get("length", 0.0)
    speed_kph = data.get("speed_kph", 0.0)
    if speed_kph > 0:
        speed_m_s = speed_kph * 1000.0 / 3600.0
        data["travel_time"] = length_m / speed_m_s
    else:
        data["travel_time"] = float("inf")

G = G.to_undirected()

nodes = set(G.nodes)

# -----------------------------
# PRECOMPUTE COVERAGE SETS
# -----------------------------
print("Computing coverage sets (this may take a while)...")

coverage = {}

# Parallelize coverage set computation across nodes using threads.
nodes_list = list(nodes)
workers_cov = min(32, (os.cpu_count() or 1) + 4)

def _compute_coverage(node):
    lengths = nx.single_source_dijkstra_path_length(
        G,
        node,
        cutoff=MAX_RESPONSE_TIME_SEC,
        weight="travel_time"
    )
    return node, set(lengths.keys())

with ThreadPoolExecutor(max_workers=workers_cov) as ex:
    futures = [ex.submit(_compute_coverage, n) for n in nodes_list]
    for fut in tqdm(as_completed(futures), total=len(futures)):
        n, covered = fut.result()
        coverage[n] = covered

# -----------------------------
# GREEDY SET COVER
# -----------------------------
print("Selecting fire stations...")
uncovered = set(nodes)
firestations = []

while uncovered:
    best_node = None
    best_covered = set()

    for candidate, covered_nodes in coverage.items():
        newly_covered = covered_nodes & uncovered
        if len(newly_covered) > len(best_covered):
            best_node = candidate
            best_covered = newly_covered

    if best_node is None:
        raise RuntimeError("Coverage failed: graph may be disconnected")

    firestations.append(best_node)
    uncovered -= best_covered

    print(
        f"Added station {len(firestations)} | "
        f"Covered {len(best_covered)} nodes | "
        f"Remaining {len(uncovered)}"
    )
    print(firestations)

# -----------------------------
# COMPUTE SERVICE DISTANCE PER NODE
# -----------------------------
G_undirected = G.to_undirected()

nodes = list(G_undirected.nodes)

# -----------------------------
# DEMAND NODES (intersections)
# -----------------------------
print("Selecting demand nodes...")
demand_nodes = nodes


print("Computing service distances...")
service_distance = {node: float('inf') for node in nodes}

def _distances_from_station(station):
    """Compute single-source shortest path lengths (by 'length') from a station."""
    return nx.single_source_dijkstra_path_length(G_undirected, station, weight="length")

print("Computing service distances (parallel over stations)...")
workers_sd = min(32, (os.cpu_count() or 1) + 2)
with ThreadPoolExecutor(max_workers=workers_sd) as exe:
    # compute distance dicts from each station in parallel
    results = list(tqdm(exe.map(_distances_from_station, firestations), total=len(firestations)))

for dist_dict in results:
    for node, d in dist_dict.items():
        # keep the minimum distance across stations
        if d < service_distance[node]:
            service_distance[node] = d

# -----------------------------
# SAVE AS COORDINATES
# -----------------------------
print("Saving solution...")
solution = {
    "firestations": [str(station) for station in firestations],
    "nodes": {},
    "service_distance": service_distance,
    "location": PLACE_NAME,
    "speed_increase": SPEED_INCREASE_KPH
}

for station in firestations:
    solution['nodes'][str(station)] = [{"x": G.nodes[station]["x"], "y": G.nodes[station]['y']}]

with open(OUTPUT_FILE, "w") as f:
    json.dump(solution, f)

print(f"Done. Placed {len(firestations)} fire stations.")
