import pandas as pd
import math
from shapely.geometry import Polygon, MultiPolygon, LineString, Point
from shapely.ops import unary_union, polygonize
import geopandas as gpd
from sklearn.cluster import DBSCAN
from pyproj import Transformer
import numpy as np
from collections import defaultdict
from scipy.spatial.distance import pdist
from scipy.spatial import Voronoi
from config import DEFAULT_GEOGRAPHIC_CRS, DEFAULT_PROJECTED_CRS

def build_outer_polygon_from_survey(survey: dict) -> Polygon:
    coords_str = survey["results"][0]["polygon"]
    coords = [(float(lng), float(lat)) for lng, lat in (pair.split(',') for pair in coords_str.split())]
    assert coords[0] == coords[-1], "Polygon ring must be closed"
    return Polygon(coords)

def create_geodataframe_from_tree_data(tree_data: list[dict], crs: str = DEFAULT_GEOGRAPHIC_CRS) -> gpd.GeoDataFrame:
    # {RL 28/06/2025} CRS conversion is required to calculate the buffer radius. Input data is in EPSG:4326 (WGS84), which uses degrees for lat/lng and needs converting to EPSG:32734, which uses meters.
    tree_data_frame = pd.DataFrame(tree_data)
    return gpd.GeoDataFrame(
        tree_data_frame,
        geometry=gpd.points_from_xy(tree_data_frame["lng"], tree_data_frame["lat"]),
        crs=crs,
    )

def create_tree_polygons(tree_data: list[dict], epsg: int = DEFAULT_PROJECTED_CRS) -> list:
    required_keys = {"lat", "lng", "area"}
    for tree in tree_data:
        if not required_keys.issubset(tree):
            raise ValueError(f"Missing one of {required_keys} in tree data: {tree}")
        
    tree_data_frame_geo = create_geodataframe_from_tree_data(tree_data)
    tree_data_frame_projected = tree_data_frame_geo.to_crs(epsg=epsg)

    def calculate_buffer_radius(area):
        return math.sqrt(area / math.pi)

    tree_data_frame_projected["geometry"] = tree_data_frame_projected.apply(
        lambda row: row.geometry.buffer(calculate_buffer_radius(row["area"])), axis=1
    )

    tree_latlng = reproject_geodataframe(tree_data_frame_projected, int(DEFAULT_GEOGRAPHIC_CRS.split(":")[-1]))

    return list(tree_latlng["geometry"])

def create_missing_tree_polygons(
    missing_coords: list[dict],
    placeholder_area_m2: float = 1.0,
    epsg_metric: int = 32734,
) -> list:
    def buffer_radius(area):
        return math.sqrt(area / math.pi)

    # Create Point geometries from dicts: Point(longitude, latitude)
    df = gpd.GeoDataFrame(
        geometry=[Point(coord["lng"], coord["lat"]) for coord in missing_coords],
        crs="EPSG:4326",
    )
    df_metric = df.to_crs(epsg=epsg_metric)

    radius = buffer_radius(placeholder_area_m2)
    df_metric["geometry"] = df_metric["geometry"].buffer(radius)

    df_latlng = df_metric.to_crs("EPSG:4326")
    return list(df_latlng.geometry)

def cluster_overlapping_positions(positions, spacing):
    """
    Merge overlapping missing positions into centralized points
    Rules:
    1. If a missing tree is not touching another missing tree, continue to flag as missing tree
    2. If missing trees are overlapping, combine them and return the centralized point
    """
    if not positions:
        return positions
    
    # Define overlap threshold - positions closer than this will be merged
    overlap_threshold = spacing * 0.6
    
    print(f"\n=== CLUSTERING DEBUG ===")
    print(f"Input positions: {len(positions)}")
    print(f"Overlap threshold: {overlap_threshold:.2f}m")
    
    # First, let's check all pairwise distances to see what should be clustered
    print(f"\nPairwise distances:")
    for i in range(len(positions)):
        for j in range(i + 1, len(positions)):
            dist = np.sqrt((positions[i]['x'] - positions[j]['x'])**2 + 
                          (positions[i]['y'] - positions[j]['y'])**2)
            should_cluster = "YES" if dist <= overlap_threshold else "NO"
    
    clustered = []
    processed = set()
    
    for i, current_pos in enumerate(positions):
        if i in processed:
            continue
                    
        # Start a new cluster with current position
        cluster = [current_pos]
        cluster_indices = {i}
        
        # Find all positions that overlap with positions in current cluster
        # Use a queue to handle transitive overlaps (A overlaps B, B overlaps C)
        queue = [i]
        
        while queue:
            current_idx = queue.pop(0)
            current_position = positions[current_idx]
                        
            # Check all remaining unprocessed positions
            for j, other_pos in enumerate(positions):
                if j in cluster_indices or j in processed:
                    continue
                    
                # Calculate distance between current position and other position
                distance = np.sqrt((current_position['x'] - other_pos['x'])**2 + 
                                 (current_position['y'] - other_pos['y'])**2)
                                
                # If positions overlap, add to cluster
                if distance <= overlap_threshold:
                    print(f"    -> Adding position {j} to cluster (distance {distance:.2f} <= {overlap_threshold:.2f})")
                    cluster.append(other_pos)
                    cluster_indices.add(j)
                    queue.append(j)  # Check this new position for more overlaps
        
        # Mark all positions in this cluster as processed
        processed.update(cluster_indices)
        
        # Process the cluster according to rules
        if len(cluster) == 1:
            # Rule 1: Single position (not touching others), keep as is
            clustered.append(current_pos)
        else:
            # Rule 2: Multiple overlapping positions, create centralized point
            center_x = np.mean([p['x'] for p in cluster])
            center_y = np.mean([p['y'] for p in cluster])
            
            print(f"  -> Creating centralized point at ({center_x:.1f}, {center_y:.1f})")
            
            # Use best metrics from the cluster
            best_distance = min(p['distance_to_nearest'] for p in cluster)
            min_nearby_count = min(p['nearby_tree_count'] for p in cluster)
            
            # Create centralized position
            clustered_position = {
                'geometry': Point(center_x, center_y),
                'x': center_x,
                'y': center_y,
                'distance_to_nearest': best_distance,
                'nearby_tree_count': min_nearby_count,
                'cluster_size': len(cluster)
            }
            
            clustered.append(clustered_position)
    
    return clustered

def find_missing_tree_positions(tree_data: list[dict], 
                                outer_polygon,
                                epsg_metric: int = DEFAULT_PROJECTED_CRS,
                                tree_spacing: float = 4.0) -> dict:
    
    tree_data_frame = pd.DataFrame(tree_data)

    # {RL 28/06/2025} CRS conversion is required to calculate the buffer radius. Input data is in EPSG:4326 (WGS84), which uses degrees for lat/lng and needs converting to EPSG:32734, which uses meters.
    tree_data_frame_crs = gpd.GeoDataFrame(
        tree_data_frame, geometry=gpd.points_from_xy(tree_data_frame["lng"], tree_data_frame["lat"]), crs=DEFAULT_GEOGRAPHIC_CRS
    )
    
    print(f"Total input trees: {len(tree_data_frame_crs)}")
    
    tree_gdf_proj = tree_data_frame_crs.to_crs(epsg=epsg_metric)
    outer_proj = gpd.GeoSeries([outer_polygon], crs="EPSG:4326").to_crs(epsg=epsg_metric).iloc[0]
    
    missing_positions = find_gaps_in_orchard(tree_gdf_proj, outer_proj, tree_spacing)
    
    print(f"Found {len(missing_positions)} potential missing tree positions")
    
    return format_results(tree_gdf_proj, missing_positions, epsg_metric)

def create_custom_buffer(polygon, normal_buffer, bottom_buffer, left_buffer):
    """Create a custom inward buffer with larger buffers on bottom and left edges"""
    minx, miny, maxx, maxy = polygon.bounds
    
    # Get exterior coordinates
    exterior_coords = list(polygon.exterior.coords)
    buffered_coords = []
    
    # Calculate tolerances for edge detection
    width = maxx - minx
    height = maxy - miny
    horizontal_tolerance = width * 0.1   # 10% of width
    vertical_tolerance = height * 0.1    # 10% of height
    
    for i, (x, y) in enumerate(exterior_coords[:-1]):  # Skip last point (duplicate of first)
        # Determine which edge this point belongs to
        is_bottom = y <= (miny + vertical_tolerance)
        is_left = x <= (minx + horizontal_tolerance)
        is_top = y >= (maxy - vertical_tolerance)
        is_right = x >= (maxx - horizontal_tolerance)
        
        # Calculate inward movement based on edge
        if is_bottom and is_left:
            # Corner: apply both buffers
            buffered_coords.append((x + left_buffer, y + bottom_buffer))
        elif is_bottom:
            # Bottom edge: move up
            buffered_coords.append((x, y + bottom_buffer))
        elif is_left:
            # Left edge: move right
            buffered_coords.append((x + left_buffer, y))
        else:
            # Top or right edges: use normal buffer toward center
            center_x = minx + width / 2
            center_y = miny + height / 2
            
            # Move toward center by normal_buffer distance
            to_center_x = center_x - x
            to_center_y = center_y - y
            distance = np.sqrt(to_center_x**2 + to_center_y**2)
            
            if distance > 0:
                norm_x = to_center_x / distance
                norm_y = to_center_y / distance
                buffered_coords.append((x + norm_x * normal_buffer, y + norm_y * normal_buffer))
            else:
                buffered_coords.append((x, y))
    
    # Close the polygon
    buffered_coords.append(buffered_coords[0])
    
    try:
        return Polygon(buffered_coords)
    except:
        # Fallback to simple buffer if custom buffer fails
        return polygon.buffer(-normal_buffer)
    
def find_gaps_in_orchard(existing_trees, outer_polygon, spacing=4.0):    
    existing_coords = [(pt.x, pt.y) for pt in existing_trees.geometry]
    existing_points = np.array(existing_coords)
    minx, miny, maxx, maxy = outer_polygon.bounds
    
    # Create buffer zones around existing trees to prevent overlap
    tree_radius = spacing * 0.4
    existing_tree_buffers = [Point(x, y).buffer(tree_radius) for x, y in existing_coords]
    
    grid_spacing = spacing * 0.75
    
    x_coords = np.arange(minx, maxx + grid_spacing, grid_spacing)
    y_coords = np.arange(miny, maxy + grid_spacing, grid_spacing)
    
    potential_positions = []
    
    for y in y_coords:
        for x in x_coords:
            test_point = Point(x, y)
            
            # Only consider points inside the orchard boundary
            if not outer_polygon.contains(test_point):
                continue
            
            # Check if this position overlaps with any existing tree
            overlaps_existing = any(buffer.contains(test_point) for buffer in existing_tree_buffers)
            if overlaps_existing:
                continue
                
            # Check distances to existing trees
            distances_to_existing = np.sqrt((existing_points[:, 0] - x)**2 + 
                                          (existing_points[:, 1] - y)**2)
            
            min_distance = np.min(distances_to_existing)
            
            # Position is a candidate if it fits the gap criteria
            min_threshold = spacing * 0.8
            max_threshold = spacing * 2.5
            
            if min_threshold < min_distance < max_threshold:
                nearby_trees = np.sum(distances_to_existing < spacing * 1.5)
                
                if nearby_trees < 4:
                    potential_positions.append({
                        'geometry': test_point,
                        'x': x,
                        'y': y,
                        'distance_to_nearest': min_distance,
                        'nearby_tree_count': nearby_trees
                    })
    
    # Apply custom buffer filtering
    normal_buffer_distance = spacing * 2
    bottom_buffer_distance = spacing * 3.5
    left_buffer_distance = spacing * 3.0
    
    inner_boundary = create_custom_buffer(outer_polygon, normal_buffer_distance, 
                                        bottom_buffer_distance, left_buffer_distance)
    
    filtered_positions = []
    for pos in potential_positions:
        if inner_boundary.contains(pos['geometry']):
            final_check_radius = spacing * 0.4 * 0.8
            test_buffer = pos['geometry'].buffer(final_check_radius)
            
            no_final_overlap = not any(
                test_buffer.intersects(Point(x, y).buffer(spacing * 0.4 * 0.5)) 
                for x, y in existing_coords
            )
            
            if no_final_overlap:
                filtered_positions.append(pos)
    
    # Apply clustering rules: merge overlapping positions
    clustered_positions = cluster_overlapping_positions(filtered_positions, spacing)
    
    return clustered_positions

def format_results(existing_trees, missing_positions, epsg_metric):    
    # Convert existing trees back to WGS84
    existing_coords = []
    for idx, tree in existing_trees.iterrows():
        point_wgs = gpd.GeoSeries([tree.geometry], crs=epsg_metric).to_crs("EPSG:4326").iloc[0]
        existing_coords.append({
            "lat": point_wgs.y,
            "lng": point_wgs.x,
            "id": idx
        })
    
    # First, convert all missing positions to WGS84 and create initial missing_coords
    initial_missing_coords = []
    for idx, pos in enumerate(missing_positions):
        point_wgs = gpd.GeoSeries([pos['geometry']], crs=epsg_metric).to_crs("EPSG:4326").iloc[0]
        
        # Enhanced confidence calculation with cluster info
        distance = pos['distance_to_nearest']
        nearby_count = pos.get('nearby_tree_count', 0)
        cluster_size = pos.get('cluster_size', 1)
        
        # Factor in distance, surrounding tree density, and clustering
        if distance > 8.0 and nearby_count <= 1:
            confidence = "high"
        elif distance > 6.0 and nearby_count <= 2:
            confidence = "medium"
        elif distance > 4.5 and nearby_count <= 3:
            confidence = "low"
        else:
            confidence = "very_low"
        
        # Boost confidence slightly for clustered positions (multiple detections)
        if cluster_size > 1 and confidence == "low":
            confidence = "medium"
        elif cluster_size > 2 and confidence == "medium":
            confidence = "high"
        
        missing_coord = {
            "lat": point_wgs.y,
            "lng": point_wgs.x,
            "confidence": confidence,
            "distance_to_nearest": round(distance, 1),
            "nearby_tree_count": nearby_count,
            "original_pos": pos  # Keep reference to original position for clustering
        }
        
        # Add cluster info if position was merged from multiple detections
        if cluster_size > 1:
            missing_coord["merged_from"] = cluster_size
        
        initial_missing_coords.append(missing_coord)
    
    # Filter out very low confidence results before clustering
    filtered_coords = [m for m in initial_missing_coords if m["confidence"] != "very_low"]
    
    print(f"\n=== CLUSTERING IN FORMAT_RESULTS ===")
    print(f"Before clustering: {len(filtered_coords)} positions")
    
    # Now cluster overlapping positions in projected coordinates
    tree_spacing = 4.0  # Default spacing
    overlap_threshold = tree_spacing * 1.8  # Increased threshold to catch positions within ~7m
    
    # First, let's debug the distances between all positions
    print("Pairwise distances:")
    for i in range(len(filtered_coords)):
        for j in range(i + 1, len(filtered_coords)):
            pos1 = filtered_coords[i]['original_pos']
            pos2 = filtered_coords[j]['original_pos']
            distance = np.sqrt((pos1['x'] - pos2['x'])**2 + (pos1['y'] - pos2['y'])**2)
            should_cluster = "YES" if distance <= overlap_threshold else "NO"
            print(f"Position {i} to {j}: {distance:.2f}m - Should cluster: {should_cluster}")
    
    clustered_coords = []
    processed = set()
    
    for i, current_coord in enumerate(filtered_coords):
        if i in processed:
            continue
            
        # Start a new cluster with current position
        cluster = [current_coord]
        cluster_indices = {i}
        
        # Use a queue to handle transitive overlaps (A overlaps B, B overlaps C)
        queue = [i]
        
        while queue:
            current_idx = queue.pop(0)
            current_pos = filtered_coords[current_idx]['original_pos']
            current_x, current_y = current_pos['x'], current_pos['y']
            
            # Check all remaining unprocessed positions
            for j, other_coord in enumerate(filtered_coords):
                if j in cluster_indices or j in processed:
                    continue
                    
                other_pos = other_coord['original_pos']
                other_x, other_y = other_pos['x'], other_pos['y']
                
                # Calculate distance in projected coordinates (meters)
                distance = np.sqrt((current_x - other_x)**2 + (current_y - other_y)**2)
                
                # If positions overlap, add to cluster
                if distance <= overlap_threshold:
                    print(f"Clustering positions {current_idx} and {j} (distance: {distance:.2f}m)")
                    cluster.append(other_coord)
                    cluster_indices.add(j)
                    queue.append(j)  # Check this new position for more overlaps
        
        # Mark all positions in this cluster as processed
        processed.update(cluster_indices)
        
        # Process the cluster
        if len(cluster) == 1:
            # Single position, keep as is but remove original_pos reference
            coord = cluster[0].copy()
            del coord['original_pos']
            clustered_coords.append(coord)
        else:
            # Multiple overlapping positions, create averaged position
            print(f"Merging {len(cluster)} overlapping positions into one")
            
            # Average the lat/lng coordinates
            avg_lat = np.mean([c['lat'] for c in cluster])
            avg_lng = np.mean([c['lng'] for c in cluster])
            
            # Use best metrics from the cluster
            best_distance = min(c['distance_to_nearest'] for c in cluster)
            min_nearby_count = min(c['nearby_tree_count'] for c in cluster)
            best_confidence = max(cluster, key=lambda c: {"high": 3, "medium": 2, "low": 1}[c['confidence']])['confidence']
            
            # Create merged position
            merged_coord = {
                "lat": avg_lat,
                "lng": avg_lng,
                "confidence": best_confidence,
                "distance_to_nearest": round(best_distance, 1),
                "nearby_tree_count": min_nearby_count,
                "merged_from": len(cluster)
            }
            
            clustered_coords.append(merged_coord)
    
    print(f"After clustering: {len(clustered_coords)} positions")
    print(f"Reduction: {len(filtered_coords) - len(clustered_coords)} positions merged")
    
    return {
        "missing_coords": clustered_coords,
        "existing_tree_coords": existing_coords,
        "summary": {
            "total_existing": len(existing_coords),
            "total_missing": len(clustered_coords),  # This should now be 4
            "high_confidence": len([m for m in clustered_coords if m["confidence"] == "high"]),
            "medium_confidence": len([m for m in clustered_coords if m["confidence"] == "medium"]),
            "low_confidence": len([m for m in clustered_coords if m["confidence"] == "low"]),
            "clustered_results": len([m for m in clustered_coords if m.get("merged_from", 1) > 1]),
            "individual_results": len([m for m in clustered_coords if m.get("merged_from", 1) == 1])
        }
    }

def reproject_geodataframe(gdf: gpd.GeoDataFrame, epsg: int) -> gpd.GeoDataFrame:
    return gdf.to_crs(epsg=epsg)
