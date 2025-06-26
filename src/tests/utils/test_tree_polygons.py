from utils.spatial import create_tree_polygons

def test_tree_polygon_count():
    trees = [{"lat": -32.3, "lng": 18.8, "area": 20}, {"lat": -32.31, "lng": 18.81, "area": 25}]
    polygons = create_tree_polygons(trees)
    assert len(polygons) == 2
