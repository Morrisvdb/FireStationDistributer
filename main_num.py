# OLD SCRIPT
import osmnx as ox
import networkx as nx
import geopandas as gpd
import numpy as np
import json
import tqdm
import numbers

# -----------------------------
# CONFIG
# -----------------------------
FILE_NAME = 'data/map.osm'
PLACE_NAME = "Nieuwegein, Utrecht, Netherlands"
NUM_STATIONS = 5
OUTPUT_FILE = "firestation_solution.json"

# -----------------------------
# LOAD ROAD NETWORK
# -----------------------------
print("Loading road network...")
G = ox.graph_from_place(
    PLACE_NAME,
    network_type="drive",
    
    
# G = ox.graph_from_xml(
#     FILE_NAME,
    simplify=True
)

G = ox.add_edge_bearings(G)

# Convert to undirected for distance computations
G_undirected = G.to_undirected()

nodes = list(G_undirected.nodes)

# -----------------------------
# DEMAND NODES (intersections)
# -----------------------------
print("Selecting demand nodes...")
demand_nodes = nodes

# -----------------------------
# K-CENTER GREEDY ALGORITHM
# -----------------------------
def greedy_k_center(G, demand_nodes, k):
    centers = [np.random.choice(demand_nodes)]

    for _ in tqdm.tqdm(range(1, k)):
        max_dist = -1
        next_center = None

        for node in demand_nodes:
            min_dist = min(
                nx.shortest_path_length(G, node, c, weight="length")
                for c in centers
            )
            if min_dist > max_dist:
                max_dist = min_dist
                next_center = node

        centers.append(next_center)

    return centers

print("Computing optimal fire station locations...")
firestations = greedy_k_center(G_undirected, demand_nodes, NUM_STATIONS)

# -----------------------------
# COMPUTE SERVICE DISTANCE PER NODE
# -----------------------------
print("Computing service distances...")
service_distance = {}

for node in tqdm.tqdm(demand_nodes):
    service_distance[node] = min(
        nx.shortest_path_length(G_undirected, node, fs, weight="length")
        for fs in firestations
    )

# -----------------------------
# SAVE RESULTS
# -----------------------------
print("Saving results...")
data = {
    "firestations": firestations,
    "service_distance": service_distance,
    "nodes": {
        str(n): {
            "x": G.nodes[n]["x"],
            "y": G.nodes[n]["y"]
        } for n in firestations
    }
}


def to_serializable(obj):
    """Recursively convert numpy / pandas scalar and array types to
    native Python types so json.dump can serialize them.

    Handles:
      - numpy.integer -> int
      - numpy.floating -> float
      - numpy.ndarray -> list
      - other iterables (list/tuple/set) -> list
      - dict keys coerced to str (JSON requires string keys)
    """
    # numpy scalars
    try:
        import numpy as _np
        if isinstance(obj, _np.integer):
            return int(obj)
        if isinstance(obj, _np.floating):
            return float(obj)
        if isinstance(obj, _np.ndarray):
            return obj.tolist()
    except Exception:
        # numpy may not be available or import failed; continue
        pass

    # built-in numeric types (no change)
    if isinstance(obj, (str, bool)) or obj is None:
        return obj

    if isinstance(obj, numbers.Integral) and not isinstance(obj, bool):
        return int(obj)
    if isinstance(obj, numbers.Real):
        return float(obj) if not isinstance(obj, int) else int(obj)

    # dict -> convert keys to str and values recursively
    if isinstance(obj, dict):
        return {str(k): to_serializable(v) for k, v in obj.items()}

    # iterable -> list of serializable items
    if isinstance(obj, (list, tuple, set)):
        return [to_serializable(v) for v in obj]

    # fallback: return as-is (json.dump will raise if still not serializable)
    return obj

with open(OUTPUT_FILE, "w") as f:
    serializable = to_serializable(data)
    json.dump(serializable, f, indent=2)

print("Done.")
