import pandas as pd
import math
from shapely.geometry import Polygon, Point
from shapely.strtree import STRtree
import geopandas as gpd
import numpy as np
from scipy.spatial import cKDTree
from src.config.settings import (
    BOTTOM_BUFFER_MULTIPLIER,
    DEFAULT_GEOGRAPHIC_CRS,
    DEFAULT_PROJECTED_CRS,
    GRID_SPACING_MULTIPLIER,
    HIGH_CONFIDENCE_DISTANCE_THRESHOLD,
    LEFT_BUFFER_MULTIPLIER,
    MAX_DISTANCE_MULTIPLIER,
    MAX_NEARBY_TREES,
    MIN_DISTANCE_MULTIPLIER,
    NEARBY_SEARCH_MULTIPLIER,
    NORMAL_BUFFER_MULTIPLIER,
    OVERLAP_THRESHOLD_METRES,
    TREE_RADIUS_MULTIPLIER,
    TREE_SPACING,
)
from src.validation.spatial import validate_tree_data


def build_outer_polygon_from_survey(survey: dict) -> Polygon:
    coords_str = survey["results"][0]["polygon"]
    coords = [
        (float(lng), float(lat))
        for lng, lat in (pair.split(",") for pair in coords_str.split())
    ]
    assert coords[0] == coords[-1], "Polygon ring must be closed"
    return Polygon(coords)


def cluster_missing_coords(missing_coords):
    if not missing_coords:
        return []

    # 🤖 Claude: Use spatial indexing for clustering
    points = np.array([[coord["x"], coord["y"]] for coord in missing_coords])
    tree = cKDTree(points)

    clustered = []
    used = set()

    for i, coord1 in enumerate(missing_coords):
        if i in used:
            continue

        # 🤖 Claude: Find all points within threshold distance
        indices = tree.query_ball_point([coord1["x"], coord1["y"]], OVERLAP_THRESHOLD_METRES)
        cluster_indices = [idx for idx in indices if idx not in used]

        if not cluster_indices:
            continue

        cluster = [missing_coords[idx] for idx in cluster_indices]
        used.update(cluster_indices)
        clustered.append(collapse_cluster(cluster))

    return clustered


def collapse_cluster(cluster):
    if len(cluster) == 1:
        return {k: v for k, v in cluster[0].items() if k not in ["x", "y"]}

    return {
        "confidence": max(
            cluster, key=lambda c: {"high": 3, "medium": 2, "low": 1}[c["confidence"]]
        )["confidence"],
        "distance_to_nearest": round(min(c["distance_to_nearest"] for c in cluster), 1),
        "lat": np.mean([c["lat"] for c in cluster]),
        "lng": np.mean([c["lng"] for c in cluster]),
        "merged_from": len(cluster),
    }


def create_custom_buffer(polygon, normal_buffer, bottom_buffer, left_buffer):
    minx, miny, maxx, maxy = polygon.bounds
    width, height = maxx - minx, maxy - miny
    htol, vtol = width * 0.1, height * 0.1  # {RL 28/05/2025} 10% buffer
    cx, cy = minx + width / 2, miny + height / 2

    def move_point(x, y):
        is_bottom = y <= (miny + vtol)
        is_left = x <= (minx + htol)

        if is_bottom and is_left:
            return (x + left_buffer, y + bottom_buffer)
        elif is_bottom:
            return (x, y + bottom_buffer)
        elif is_left:
            return (x + left_buffer, y)
        else:
            dx, dy = cx - x, cy - y
            dist = np.hypot(dx, dy)
            if dist == 0:
                return (x, y)
            return (x + (dx / dist) * normal_buffer, y + (dy / dist) * normal_buffer)

    coords = polygon.exterior.coords[:-1]
    buffered_coords = [move_point(x, y) for x, y in coords]
    buffered_coords.append(buffered_coords[0])

    try:
        return Polygon(buffered_coords)
    except Exception:
        print("Custom buffer failed: Falling back to normal buffer")
        return polygon.buffer(-normal_buffer)


def create_geodataframe_from_tree_data(
    tree_data: list[dict],
    to_projected_crs: bool = True,
    crs: str = DEFAULT_GEOGRAPHIC_CRS,
    projected_crs: int = DEFAULT_PROJECTED_CRS,
) -> gpd.GeoDataFrame:
    tree_data_frame = pd.DataFrame(tree_data)
    gdf = gpd.GeoDataFrame(
        tree_data_frame,
        geometry=gpd.points_from_xy(tree_data_frame["lng"], tree_data_frame["lat"]),
        crs=crs,
    )
    # {RL 28/06/2025} CRS conversion is required to calculate the metric distance. Input data is in EPSG:4326 (WGS84),
    # which uses degrees for lat/lng and needs converting to EPSG:32734, which uses meters.
    if to_projected_crs:
        return gdf.to_crs(epsg=projected_crs)
    return gdf


def create_inner_boundary(outer_polygon, spacing):
    return create_custom_buffer(
        outer_polygon,
        spacing * NORMAL_BUFFER_MULTIPLIER,
        spacing * BOTTOM_BUFFER_MULTIPLIER,
        spacing * LEFT_BUFFER_MULTIPLIER,
    )


def create_tree_polygons(
    tree_data: list[dict], epsg: int = DEFAULT_PROJECTED_CRS
) -> list:
    print(f"Total input trees: {len(tree_data)}")
    validate_tree_data(tree_data)

    tree_data_frame_projected = create_geodataframe_from_tree_data(tree_data)

    def calculate_buffer_radius(area):
        return math.sqrt(area / math.pi)

    tree_data_frame_projected["geometry"] = tree_data_frame_projected.apply(
        lambda row: row.geometry.buffer(calculate_buffer_radius(row["area"])), axis=1
    )

    tree_geographic = tree_data_frame_projected.to_crs(epsg=epsg)
    return list(tree_geographic["geometry"])


def extract_existing_tree_coords(existing_trees, epsg_metric):
    coords = []
    for idx, tree in existing_trees.iterrows():
        point_wgs = (
            gpd.GeoSeries([tree.geometry], crs=epsg_metric)
            .to_crs(DEFAULT_GEOGRAPHIC_CRS)
            .iloc[0]
        )
        coords.append({"lat": point_wgs.y, "lng": point_wgs.x, "id": idx})
    return coords


def extract_high_confidence_missing_coords(missing_positions, epsg_metric):
    coords = []
    for pos in missing_positions:
        point_wgs = (
            gpd.GeoSeries([pos["geometry"]], crs=epsg_metric)
            .to_crs(DEFAULT_GEOGRAPHIC_CRS)
            .iloc[0]
        )

        distance = pos["distance_to_nearest"]
        nearby_count = pos.get("nearby_tree_count", 0)

        if (
            distance > HIGH_CONFIDENCE_DISTANCE_THRESHOLD
            and nearby_count < MAX_NEARBY_TREES
        ):
            confidence = "high"
        else:
            continue

        coords.append(
            {
                "confidence": confidence,
                "distance_to_nearest": round(distance, 1),
                "lat": point_wgs.y,
                "lng": point_wgs.x,
                "nearby_tree_count": nearby_count,
                "x": pos["x"],
                "y": pos["y"],
            }
        )

    return coords


def extract_tree_coordinates(existing_trees):
    return [(pt.x, pt.y) for pt in existing_trees.geometry]


def filter_positions_within_inner_boundary(
    potential_positions, inner_boundary, existing_tree_spatial_index, tree_kdtree, existing_coords, spacing
):
    filtered_positions = []
    final_check_radius = spacing * TREE_RADIUS_MULTIPLIER * MIN_DISTANCE_MULTIPLIER

    # {Rl 28/06/2025} Use a smaller buffer to avoid false positives near tree edges
    overlap_check_radius = spacing * TREE_RADIUS_MULTIPLIER * 0.5

    for pos in potential_positions:
        if not inner_boundary.contains(pos["geometry"]):
            continue

        # 🤖 Claude: Use spatial index for faster intersection checks
        test_buffer = pos["geometry"].buffer(final_check_radius)
        nearby_trees = list(existing_tree_spatial_index.query(test_buffer))

        if not any(test_buffer.intersects(tree_geom.buffer(overlap_check_radius)) for tree_geom in nearby_trees):
            filtered_positions.append(pos)

    return filtered_positions


def find_gaps_in_orchard(existing_trees, outer_polygon, spacing):
    existing_coords = extract_tree_coordinates(existing_trees)
    existing_points = np.array(existing_coords)

    print("......Creating tree buffers")
    tree_geometries = [Point(x, y) for x, y in existing_coords]
    existing_tree_spatial_index = STRtree(tree_geometries)
    tree_kdtree = cKDTree(existing_points)

    print("......Generating candidate positions")
    potential_positions = generate_candidate_positions_optimized(
        outer_polygon, existing_tree_spatial_index, tree_kdtree, existing_points, spacing
    )

    print("......Generating inner boundary")
    inner_boundary = create_inner_boundary(outer_polygon, spacing)

    print("......Filtering positions within inner boundary")
    return filter_positions_within_inner_boundary(
        potential_positions, inner_boundary, existing_tree_spatial_index, tree_kdtree, existing_coords, spacing
    )


def generate_candidate_positions_optimized(
    outer_polygon, existing_tree_spatial_index, tree_kdtree, existing_points, spacing
):
    """Optimized version using spatial indexing and vectorized operations"""
    grid_spacing = spacing * GRID_SPACING_MULTIPLIER
    minx, miny, maxx, maxy = outer_polygon.bounds

    # 🤖 Claude: Create grid points
    x_coords = np.arange(minx, maxx + grid_spacing, grid_spacing)
    y_coords = np.arange(miny, maxy + grid_spacing, grid_spacing)

    # 🤖 Claude: Create meshgrid for vectorized operations
    X, Y = np.meshgrid(x_coords, y_coords)
    grid_points = np.column_stack([X.ravel(), Y.ravel()])

    tree_radius = spacing * TREE_RADIUS_MULTIPLIER
    min_threshold = spacing * MIN_DISTANCE_MULTIPLIER
    max_threshold = spacing * MAX_DISTANCE_MULTIPLIER
    nearby_threshold = spacing * NEARBY_SEARCH_MULTIPLIER

    potential_positions = []

    # 🤖 Claude: Process in chunks to manage memory
    chunk_size = 10000
    for i in range(0, len(grid_points), chunk_size):
        chunk = grid_points[i:i + chunk_size]

        # 🤖 Claude: Vectorized polygon containment check
        chunk_points = [Point(x, y) for x, y in chunk]
        contained_mask = np.array([outer_polygon.contains(pt) for pt in chunk_points])

        if not np.any(contained_mask):
            continue

        valid_chunk = chunk[contained_mask]
        valid_points = [chunk_points[j] for j, mask in enumerate(contained_mask) if mask]

        # 🤖 Claude: Batch query for tree overlaps using spatial index
        tree_buffers = [pt.buffer(tree_radius) for pt in valid_points]
        overlap_mask = np.array([
            len(list(existing_tree_spatial_index.query(buffer))) > 0
            for buffer in tree_buffers
        ])

        non_overlapping_mask = ~overlap_mask
        if not np.any(non_overlapping_mask):
            continue

        final_chunk = valid_chunk[non_overlapping_mask]
        final_points = [valid_points[j] for j, mask in enumerate(non_overlapping_mask) if mask]

        # 🤖 Claude: Vectorized distance calculations using KDTree
        if len(final_chunk) > 0:
            distances, _ = tree_kdtree.query(final_chunk)

            # 🤖 Claude: Apply distance thresholds
            distance_mask = (distances > min_threshold) & (distances < max_threshold)

            for j, (point, (x, y), distance) in enumerate(zip(final_points, final_chunk, distances)):
                if not distance_mask[j]:
                    continue

                # 🤖 Claude: Count nearby trees
                nearby_indices = tree_kdtree.query_ball_point([x, y], nearby_threshold)
                nearby_count = len(nearby_indices)

                if nearby_count < MAX_NEARBY_TREES:
                    potential_positions.append({
                        "geometry": point,
                        "x": x,
                        "y": y,
                        "distance_to_nearest": distance,
                        "nearby_tree_count": nearby_count,
                    })

    return potential_positions


def find_missing_tree_positions(
    tree_data: list[dict],
    outer_polygon,
    epsg: int = DEFAULT_PROJECTED_CRS,
    tree_spacing: float = TREE_SPACING,
) -> dict:
    tree_gdf = create_geodataframe_from_tree_data(tree_data, to_projected_crs=True)
    outer_polygon_projected = (
        gpd.GeoSeries([outer_polygon], crs=DEFAULT_GEOGRAPHIC_CRS)
        .to_crs(epsg=epsg)
        .iloc[0]
    )

    missing_positions = find_gaps_in_orchard(
        tree_gdf, outer_polygon_projected, tree_spacing
    )
    return format_results(tree_gdf, missing_positions, epsg)


def format_results(existing_trees, missing_positions, epsg_metric):
    existing_coords = extract_existing_tree_coords(existing_trees, epsg_metric)
    missing_coords = extract_high_confidence_missing_coords(
        missing_positions, epsg_metric
    )
    clustered_coords = cluster_missing_coords(missing_coords)

    print(f"Identified {len(clustered_coords)} missing trees")

    return {
        "missing_coords": clustered_coords,
        "existing_tree_coords": existing_coords,
        "summary": generate_summary(existing_coords, clustered_coords),
    }


def generate_summary(existing_coords, clustered_coords):
    return {
        "total_existing": len(existing_coords),
        "total_missing": len(clustered_coords),
        "high_confidence": sum(
            1 for m in clustered_coords if m["confidence"] == "high"
        ),
        "medium_confidence": sum(
            1 for m in clustered_coords if m["confidence"] == "medium"
        ),
        "low_confidence": sum(1 for m in clustered_coords if m["confidence"] == "low"),
    }


def inner_boundary_visualisation(outer_polygon):
    normal_buffer_distance = TREE_SPACING * NORMAL_BUFFER_MULTIPLIER
    bottom_buffer_distance = TREE_SPACING * BOTTOM_BUFFER_MULTIPLIER
    left_buffer_distance = TREE_SPACING * LEFT_BUFFER_MULTIPLIER

    outer_polygon_projected = (
        gpd.GeoSeries([outer_polygon], crs=DEFAULT_GEOGRAPHIC_CRS)
        .to_crs(epsg=DEFAULT_PROJECTED_CRS)
        .iloc[0]
    )
    inner_boundary = create_custom_buffer(
        outer_polygon_projected,
        normal_buffer_distance,
        bottom_buffer_distance,
        left_buffer_distance,
    )

    return (
        gpd.GeoSeries([inner_boundary], crs=DEFAULT_PROJECTED_CRS)
        .to_crs(DEFAULT_GEOGRAPHIC_CRS)
        .iloc[0]
    )