import pandas as pd
import geopandas as gpd
import math
from shapely.geometry import Polygon, MultiPolygon
from shapely.ops import unary_union

# TODO: Replace hardcoded ploygon coords with Aerobotics data returned from /surveys/
coord_str = "18.825688993836707,-32.32741477565738 18.82707301368839,-32.32771395090236 18.82696840753681,-32.32805392157161 18.826920127774542,-32.32810831676022 18.82668945779926,-32.328899309768175 18.82535103550083,-32.32913728625483 18.825165963078803,-32.32913048693532 18.825688993836707,-32.32741477565738"
coords = [(float(lng), float(lat)) for lng, lat in (pair.split(',') for pair in coord_str.split())]

assert coords[0] == coords[-1], "Polygon ring must be closed"
outer_polygon = Polygon(coords)

# EPSG:32734 = UTM Zone 34S (metric, South Africa)
def create_tree_polygons(tree_data: list[dict], epsg: int = 32734) -> list:
    df = pd.DataFrame(tree_data)
    # EPSG:4326 = WGS84 Lat/Lon
    gdf = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df["lng"], df["lat"]), crs="EPSG:4326")
    gdf = gdf.to_crs(epsg=epsg)

    def buffer_from_area(area):
        return math.sqrt(area / math.pi)

    gdf["geometry"] = gdf.apply(lambda row: row.geometry.buffer(buffer_from_area(row["area"])), axis=1)
    return list(gdf["geometry"])

# Sample tree data
tree_data = [
    {"lat": -32.3, "lng": 18.8, "area": 20},
    {"lat": -32.31, "lng": 18.81, "area": 25},
]

# Generate tree polygons
tree_polygons = create_tree_polygons(tree_data)

# Merge tree polygons to single geometry
trees_union = unary_union(tree_polygons)

# Subtract tree areas from outer polygon to find gaps
gaps = outer_polygon.difference(trees_union)

# Filter gaps larger than 10 square meters
gap_polygons = []
if isinstance(gaps, Polygon):
    if gaps.area > 10:
        gap_polygons.append(gaps)
elif isinstance(gaps, MultiPolygon):
    gap_polygons = [g for g in gaps.geoms if g.area > 10]

print(f"Number of tree polygons: {len(tree_polygons)}")
print(f"Number of gap polygons >10m²: {len(gap_polygons)}")
