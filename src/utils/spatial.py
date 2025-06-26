import pandas as pd
import geopandas as gpd
import math
from shapely.geometry import Polygon, MultiPolygon
from shapely.ops import unary_union

def create_tree_polygons(tree_data: list[dict], epsg: int = 32734) -> list:
    df = pd.DataFrame(tree_data)

    gdf = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df["lng"], df["lat"]), crs="EPSG:4326")
    gdf_metric = gdf.to_crs(epsg=epsg)

    def buffer_from_area(area):
        return math.sqrt(area / math.pi)

    gdf_metric["geometry"] = gdf_metric.apply(
        lambda row: row.geometry.buffer(buffer_from_area(row["area"])),
        axis=1
    )

    # print("Buffered geometries in metric CRS:")
    # print(gdf_metric["geometry"])
    # print("Buffered areas in m² (metric CRS):", gdf_metric["geometry"].area)

    gdf = gdf_metric.to_crs("EPSG:4326")
  
    return list(gdf["geometry"])
 
def find_missing_tree_gaps(outer_polygon, tree_polygons, min_gap_area=5.0):
    gdf_outer = gpd.GeoSeries([outer_polygon], crs="EPSG:4326").to_crs(epsg=32734)
    outer_proj = gdf_outer.iloc[0]

    gdf_trees = gpd.GeoSeries(tree_polygons, crs="EPSG:4326").to_crs(epsg=32734)
    trees_union_proj = unary_union(gdf_trees)
    
    gaps_proj = outer_proj.difference(trees_union_proj)
    
    gap_polygons = []
    if isinstance(gaps_proj, Polygon):
        if gaps_proj.area > min_gap_area:
            gap_polygons.append(gaps_proj)
    elif isinstance(gaps_proj, MultiPolygon):
        gap_polygons = [g for g in gaps_proj.geoms if g.area > min_gap_area]

    print(f"Number of gap polygons > {min_gap_area} m²:", len(gap_polygons))

    gaps_latlng = reproject_gaps_to_latlng(gap_polygons)

    return gaps_latlng

def reproject_gaps_to_latlng(gap_polygons_proj):
    gdf = gpd.GeoDataFrame(geometry=gap_polygons_proj, crs="EPSG:32734")
    gdf_latlng = gdf.to_crs(epsg=4326)
    return list(gdf_latlng.geometry)