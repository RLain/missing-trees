from shapely.geometry import Point, Polygon
from shapely.ops import unary_union
import math
import geopandas as gpd
import pandas as pd

# Your tree data as list of dicts
tree_data = [
    {"lat": -32.3279643, "lng": 18.826872, "area": 22.667},
    {"lat": -32.3281893, "lng": 18.8263421, "area": 22.662},
]

# Step 1: Create GeoDataFrame with Points
df = pd.DataFrame(tree_data)
gdf = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df["lng"], df["lat"]), crs="EPSG:4326")

# Step 2: Project to a metric CRS (e.g., UTM zone 34S — adjust as needed)
gdf = gdf.to_crs(epsg=32734)  # EPSG:32734 = WGS84 / UTM zone 34S for southern Africa

# Step 3: Buffer using radius derived from area
def buffer_from_area(area):
    radius = math.sqrt(area / math.pi)
    return radius

gdf["geometry"] = gdf.apply(lambda row: row.geometry.buffer(buffer_from_area(row["area"])), axis=1)

# You now have tree_polygons:
tree_polygons = list(gdf["geometry"])
