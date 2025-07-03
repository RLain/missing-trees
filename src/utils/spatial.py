import numpy as np
from shapely.geometry import Polygon, Point
from typing import List, Dict, Tuple
import logging

from src.validation.spatial import validate_tree_data

# Configuration
CONFIG = {
    'BUFFER_DISTANCE': 5.0,     # meters - inward buffer from polygon edge
    'MIN_TREE_DISTANCE': 8.0,   # minimum distance from existing trees
    'MAX_TREE_DISTANCE': 25.0,  # maximum distance from existing trees
    'GRID_SPACING': 3.0,        # spacing between grid points
}

def build_outer_polygon_from_survey(survey: Dict) -> Polygon:
    coords_str = survey["results"][0]["polygon"]
    
    return parse_polygon_coords(coords_str)


def create_buffer(polygon: Polygon, distance: float) -> Polygon:
    """Create inward buffer (negative buffer) from polygon"""
    return polygon.buffer(-distance)

def generate_grid_points(polygon: Polygon, spacing: float) -> np.ndarray:
    """
    Generate grid points within polygon bounds using numpy
    Returns array of [lng, lat] coordinates
    """
    minx, miny, maxx, maxy = polygon.bounds
    
    # Generate coordinate arrays
    x_coords = np.arange(minx, maxx + spacing, spacing)
    y_coords = np.arange(miny, maxy + spacing, spacing)
    
    # Create meshgrid
    X, Y = np.meshgrid(x_coords, y_coords)
    
    # Flatten to get all coordinate pairs
    grid_points = np.column_stack([X.ravel(), Y.ravel()])
    
    return grid_points

def filter_points_in_polygon(points: np.ndarray, polygon: Polygon) -> np.ndarray:
    """
    Filter points that are contained within the polygon
    Uses vectorized operations where possible
    """
    valid_points = []
    
    # Check each point for containment
    for point in points:
        if polygon.contains(Point(point[0], point[1])):
            valid_points.append(point)
    
    return np.array(valid_points) if valid_points else np.empty((0, 2))

def calculate_distances_vectorized(candidate_points: np.ndarray, existing_trees: np.ndarray) -> np.ndarray:
    """
    Calculate minimum distance from each candidate point to all existing trees
    Uses numpy broadcasting for efficient computation
    """
    if len(existing_trees) == 0:
        return np.full(len(candidate_points), float('inf'))
    
    # Reshape for broadcasting: (n_candidates, 1, 2) and (1, n_existing, 2)
    candidates_expanded = candidate_points[:, np.newaxis, :]
    existing_expanded = existing_trees[np.newaxis, :, :]
    
    # Calculate squared distances using broadcasting
    squared_distances = np.sum((candidates_expanded - existing_expanded) ** 2, axis=2)
    
    # Get minimum distance for each candidate point
    min_distances = np.sqrt(np.min(squared_distances, axis=1))
    
    return min_distances

def find_missing_trees_numpy(
    tree_data: List[Dict],
    polygon_coords: str
) -> Dict:
    """
    NumPy-optimized version for finding missing tree positions
    
    Args:
        tree_data: List of dictionaries with 'lat', 'lng', and 'area' keys
        polygon_coords: String of polygon coordinates "lng1,lat1 lng2,lat2 ..."
    
    Returns:
        Dictionary with missing_coords, existing_tree_coords, and summary
    """
    try:
        # Parse polygon and create buffer
        polygon = parse_polygon_coords(polygon_coords)
        buffered_polygon = create_buffer(polygon, CONFIG['BUFFER_DISTANCE'])
        
        # Convert existing trees to numpy array [lng, lat]
        if tree_data:
            existing_trees = np.array([[tree['lng'], tree['lat']] for tree in tree_data])
        else:
            existing_trees = np.empty((0, 2))
        
        # Generate grid points
        grid_points = generate_grid_points(buffered_polygon, CONFIG['GRID_SPACING'])
        
        # Filter points within buffered polygon
        valid_points = filter_points_in_polygon(grid_points, buffered_polygon)
        
        if len(valid_points) == 0:
            logging.info("No valid grid points found within polygon")
            return {
                'missing_coords': [],
                'existing_tree_coords': [{'lat': tree['lat'], 'lng': tree['lng']} for tree in tree_data],
                'summary': {
                    'total_existing': len(tree_data),
                    'total_missing': 0
                }
            }
        
        # Calculate distances to existing trees
        distances = calculate_distances_vectorized(valid_points, existing_trees)
        
        # Apply distance thresholds
        distance_mask = (distances >= CONFIG['MIN_TREE_DISTANCE']) & (distances <= CONFIG['MAX_TREE_DISTANCE'])
        
        # Filter valid missing positions
        missing_points = valid_points[distance_mask]
        missing_distances = distances[distance_mask]
        
        # Format results
        missing_coords = [
            {
                'lat': float(point[1]),
                'lng': float(point[0]),
                'distance_to_nearest': round(float(distance), 1)
            }
            for point, distance in zip(missing_points, missing_distances)
        ]
        
        existing_coords = [
            {'lat': tree['lat'], 'lng': tree['lng']} 
            for tree in tree_data
        ]
        
        logging.info(f"Found {len(missing_coords)} potential missing tree positions")
        
        return {
            'missing_coords': missing_coords,
            'existing_tree_coords': existing_coords,
            'summary': {
                'total_existing': len(existing_coords),
                'total_missing': len(missing_coords)
            }
        }
        
    except Exception as e:
        logging.error(f"Error in find_missing_trees_numpy: {e}")
        raise


def parse_polygon_coords(coords_str: str) -> Polygon:
    try:
        coords = [
            (float(lng), float(lat))
            for lng, lat in (pair.split(",") for pair in coords_str.split())
        ]
        return Polygon(coords)
    except Exception as e:
        raise ValueError(f"Invalid polygon coordinates: {e}")
    
    
def process_tree_analysis(tree_survey: Dict, survey: Dict) -> Dict:
    if not tree_survey.get("results"):
        raise ValueError("No tree survey results provided")
    
    if not survey.get("results") or not survey["results"][0].get("polygon"):
        raise ValueError("No polygon data provided")
    
    tree_data = [
        {
            "lat": tree["lat"],
            "lng": tree["lng"],
            "area": tree.get("area", 10.0),  # Default area if not provided
        }
        for tree in tree_survey["results"]
    ]
    
    # Validate tree data
    validate_tree_data(tree_data)
    
    # Extract polygon
    polygon_coords = survey["results"][0]["polygon"]
    
    # Run analysis
    logging.info("Running NumPy-based tree analysis...")
    results = find_missing_trees_numpy(tree_data, polygon_coords)
    
    return results
