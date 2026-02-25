import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon, Circle

def regular_polygon(n, side_length=1.0, center=(0, 0), rotation=0):
    """
    Create a regular n-gon from side length.
    """
    cx, cy = center
    R = side_length / (2*np.sin(np.pi/n))  # circumradius from side length
    angles = np.linspace(0, 2*np.pi, n, endpoint=False) + rotation
    return np.column_stack([
        cx + R * np.cos(angles),
        cy + R * np.sin(angles)
    ])

side = 0.1
n = 12

# Dodecagon circumradius
R12 = side / (2*np.sin(np.pi/n))

# Distance between dodecagon centers in (12,12,3)
spacing = 2 * R12 * np.cos(np.pi/n)

# Hexagonal lattice vectors
v1 = np.array([spacing, 0])
v2 = np.array([spacing/2, spacing*np.sqrt(3)/2])

grid = 5

# ---------- Generate Dodecagon Centers ----------

centers = {}
for i in range(-grid, grid+1):
    for j in range(-grid, grid+1):
        centers[(i, j)] = i*v1 + j*v2

fig, ax = plt.subplots(figsize=(8, 8))

# --- Draw Dodecagons + Circumcircles ---
for c in centers.values():
    poly = regular_polygon(
        12,
        side_length=side,
        center=c,
        rotation=np.pi/12
    )
    ax.add_patch(Polygon(poly,
                         closed=True,
                         edgecolor='black',
                         facecolor='none',
                         linewidth=0.4))

    # Circumscribed circle
    ax.add_patch(Circle(c,
                        R12,
                        edgecolor='blue',
                        facecolor='none',
                        linewidth=1))

# --- Draw Triangles + Circumcircles ---

R3 = side / (2*np.sin(np.pi/3))  # triangle circumradius

for (i, j), A in centers.items():

    # upward lattice triangle
    if (i+1, j) in centers and (i, j+1) in centers:
        B = centers[(i+1, j)]
        C = centers[(i, j+1)]
        center_tri = (A + B + C) / 3
        
        tri = regular_polygon(
            3,
            side_length=side,
            center=center_tri,
            rotation=-100
        )
        ax.add_patch(Polygon(tri,
                             closed=True,
                             edgecolor='black',
                             facecolor='none',
                             linewidth=0.4))

        ax.add_patch(Circle(center_tri,
                            R3,
                            edgecolor='red',
                            facecolor='none',
                            linewidth=1.0))

    # downward lattice triangle
    if (i+1, j-1) in centers and (i+1, j) in centers:
        B = centers[(i+1, j-1)]
        C = centers[(i+1, j)]
        center_tri = (A + B + C) / 3
        
        tri = regular_polygon(
            3,
            side_length=side,
            center=center_tri,
            rotation=100
        )
        ax.add_patch(Polygon(tri,
                             closed=True,
                             edgecolor='black',
                             facecolor='none',
                             linewidth=0.4))

        ax.add_patch(Circle(center_tri,
                            R3,
                            edgecolor='red',
                            facecolor='none',
                            linewidth=1.0))
        
        
# -------- Background ---------

# img = plt.imread("./background.png")

# ax.imshow(
#     X = img,
#     )

# ---------- Display ----------

ax.set_aspect('equal')
ax.axis('off')
plt.tight_layout()
plt.show()