import pandas as pd
import math
from shapely.geometry import Polygon, Point
import geopandas as gpd
import numpy as np
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


# TODO: Step through and properly understand
def create_custom_buffer(polygon, normal_buffer, bottom_buffer, left_buffer):
    minx, miny, maxx, maxy = polygon.bounds
    width, height = maxx - minx, maxy - miny
    htol, vtol = width * 0.1, height * 0.1
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
    except:
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
    # {RL 28/06/2025} CRS conversion is required to calculate the metric distance. Input data is in EPSG:4326 (WGS84), which uses degrees for lat/lng and needs converting to EPSG:32734, which uses meters.
    if to_projected_crs:
        return gdf.to_crs(epsg=projected_crs)
    return gdf


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


def find_gaps_in_orchard(existing_trees, outer_polygon, spacing):
    existing_coords = [(pt.x, pt.y) for pt in existing_trees.geometry]

    existing_points = np.array(existing_coords)
    minx, miny, maxx, maxy = outer_polygon.bounds

    # {RL 28/06/2025} Create buffer zones around existing trees to prevent overlap
    tree_radius = spacing * TREE_RADIUS_MULTIPLIER

    existing_tree_buffers = [
        Point(x, y).buffer(tree_radius) for x, y in existing_coords
    ]

    grid_spacing = spacing * GRID_SPACING_MULTIPLIER

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
            overlaps_existing = any(
                buffer.contains(test_point) for buffer in existing_tree_buffers
            )  # {RL 28/06/2025} Future performance consideration (GPT raising: This results in O(n) operations for each grid point — very slow when you have thousands of trees. Use STRtree)
            if overlaps_existing:
                continue

            # Check distances to existing trees
            distances_to_existing = np.sqrt(
                (existing_points[:, 0] - x) ** 2 + (existing_points[:, 1] - y) ** 2
            )

            min_distance = np.min(distances_to_existing)

            # Position is a candidate if it fits the gap criteria
            min_threshold = spacing * MIN_DISTANCE_MULTIPLIER
            max_threshold = spacing * MAX_DISTANCE_MULTIPLIER

            if min_threshold < min_distance < max_threshold:
                nearby_trees = np.sum(
                    distances_to_existing < spacing * NEARBY_SEARCH_MULTIPLIER
                )

                if nearby_trees < 4:
                    potential_positions.append(
                        {
                            "geometry": test_point,
                            "x": x,
                            "y": y,
                            "distance_to_nearest": min_distance,
                            "nearby_tree_count": nearby_trees,
                        }
                    )

    # {RL 28/06/2025} ⚠️: This is not robust....wrangling the outer permimeter based on visual intel. See Known Issues I1.
    normal_buffer_distance = spacing * NORMAL_BUFFER_MULTIPLIER
    bottom_buffer_distance = spacing * BOTTOM_BUFFER_MULTIPLIER
    left_buffer_distance = spacing * LEFT_BUFFER_MULTIPLIER

    inner_boundary = create_custom_buffer(
        outer_polygon,
        normal_buffer_distance,
        bottom_buffer_distance,
        left_buffer_distance,
    )

    filtered_positions = []
    for pos in potential_positions:
        if inner_boundary.contains(pos["geometry"]):
            final_check_radius = spacing * 0.4 * 0.8
            test_buffer = pos["geometry"].buffer(final_check_radius)

            no_final_overlap = not any(
                test_buffer.intersects(
                    Point(x, y).buffer(spacing * TREE_RADIUS_MULTIPLIER * 0.5)
                )
                for x, y in existing_coords
            )

            if no_final_overlap:
                filtered_positions.append(pos)

    return filtered_positions


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
    existing_coords = []
    for idx, tree in existing_trees.iterrows():
        point_wgs = (
            gpd.GeoSeries([tree.geometry], crs=epsg_metric)
            .to_crs(DEFAULT_GEOGRAPHIC_CRS)
            .iloc[0]
        )
        existing_coords.append({"lat": point_wgs.y, "lng": point_wgs.x, "id": idx})

    # {RL 28/06/2025} Calculate confidence scoring of missing trees
    missing_coords = []
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

        missing_coords.append(
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

    # {RL 28/06/2025} Then cluster overlapping trees and average coordinates.
    clustered_coords = []
    used = set()
    overlap_threshold = OVERLAP_THRESHOLD_METRES

    for i, coord1 in enumerate(missing_coords):
        if i in used:
            continue

        cluster = [coord1]
        cluster_indices = [i]

        for j in range(i + 1, len(missing_coords)):
            if j in used:
                continue

            distance = np.sqrt(
                (coord1["x"] - missing_coords[j]["x"]) ** 2
                + (coord1["y"] - missing_coords[j]["y"]) ** 2
            )

            if distance <= overlap_threshold:
                cluster.append(missing_coords[j])
                cluster_indices.append(j)

        used.update(cluster_indices)

        if len(cluster) == 1:
            final_coord = {k: v for k, v in cluster[0].items() if k not in ["x", "y"]}
        else:
            final_coord = {
                "confidence": max(
                    cluster,
                    key=lambda c: {"high": 3, "medium": 2, "low": 1}[c["confidence"]],
                )["confidence"],
                "distance_to_nearest": round(
                    min(c["distance_to_nearest"] for c in cluster), 1
                ),
                "lat": np.mean([c["lat"] for c in cluster]),
                "lng": np.mean([c["lng"] for c in cluster]),
                "merged_from": len(cluster),
            }

        clustered_coords.append(final_coord)

    print(f"Identified {len(clustered_coords)} missing trees")

    return {
        "missing_coords": clustered_coords,
        "existing_tree_coords": existing_coords,
        "summary": {
            "total_existing": len(existing_coords),
            "total_missing": len(clustered_coords),
            "high_confidence": len(
                [m for m in clustered_coords if m["confidence"] == "high"]
            ),
            "medium_confidence": len(
                [m for m in clustered_coords if m["confidence"] == "medium"]
            ),
            "low_confidence": len(
                [m for m in clustered_coords if m["confidence"] == "low"]
            ),
        },
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
