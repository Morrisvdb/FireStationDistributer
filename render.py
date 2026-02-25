import osmnx as ox
import networkx as nx
import folium
import json
import branca.colormap as cm
from tqdm import tqdm
import sys, getopt

# -----------------------------
# CONFIG
# -----------------------------


def render_map(file, output_map):
    with open(file) as f:
        solution = json.load(f)
    
    place_name = solution['location']
    
    
    # -----------------------------
    # LOAD DATA
    # -----------------------------
    print("Loading graph...")
    G = ox.graph_from_place(
        place_name,
        network_type="drive",
        simplify=True
    )
    G = ox.add_edge_bearings(G)


    firestations = [int(n) for n in solution["firestations"]]
    service_distance = {int(k): v for k, v in solution["service_distance"].items()}

    # -----------------------------
    # COLOR MAP
    # -----------------------------
    max_dist = max(service_distance.values())
    colormap = cm.LinearColormap(
        colors=["green", "yellow", "red"],
        vmin=0,
        vmax=max_dist
    )

    # -----------------------------
    # BASE MAP
    # -----------------------------
    center = ox.graph_to_gdfs(G, nodes=True, edges=False).unary_union.centroid
    m = folium.Map(location=[center.y, center.x], zoom_start=13)

    # -----------------------------
    # DRAW ROADS
    # -----------------------------
    print("Rendering roads...")
    edges = ox.graph_to_gdfs(G, nodes=False)

    for (u, v, k), row in tqdm(edges.iterrows()):

        dist = min(
            service_distance.get(u, max_dist),
            service_distance.get(v, max_dist)
        )

        color = colormap(dist)

        if row.geometry:
            coords = [(lat, lon) for lon, lat in row.geometry.coords]
            folium.PolyLine(
                locations=coords,
                color=color,
                weight=3,
                opacity=0.8
            ).add_to(m)


    # -----------------------------
    # FIRE STATIONS
    # -----------------------------
    print("Adding fire stations...")
    for n in tqdm(firestations):
        folium.Marker(
            location=[G.nodes[n]["y"], G.nodes[n]["x"]],
            icon=folium.Icon(icon="fire", color="red"),
            popup="Fire Station"
        ).add_to(m)

    colormap.caption = "Distance to Nearest Fire Station (meters)"
    colormap.add_to(m)

    # -----------------------------
    # SAVE MAP
    # -----------------------------
    m.save(output_map)
    print(f"Map saved to {output_map}")

if __name__ == '__main__':
    # Defaults
    SOLUTION_FILE = "solution.json"

    args = sys.argv[1:]
    options = "i:"
    long_options = ["input="]

    try:
        arguments, values = getopt.getopt(args, options, long_options)
        for currentArg, currentVal in arguments:
            if currentArg in ("-i", "--input"):
                SOLUTION_FILE = currentVal
    except getopt.error as err:
        print(str(err))
    
    with open(SOLUTION_FILE) as f:
            solution = json.load(f)
            
    PLACE_NAME = solution['location']
    print("Solution was calculated for " + PLACE_NAME)

    place_stripped = PLACE_NAME.split(",")[0].lower()
    OUTPUT_MAP = place_stripped + "_firestation_map.html"
        
    render_map(file=SOLUTION_FILE, output_map=OUTPUT_MAP)