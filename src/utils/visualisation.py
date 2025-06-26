import folium
from shapely.geometry import mapping

def create_map(tree_polygons, outer_polygon, gap_polygons, center_lat=-32.315, center_lng=18.815):
    """
    Creates a folium map visualizing the outer polygon, tree polygons, and gap polygons.

    Parameters:
        tree_polygons (list): List of Shapely Polygons for trees
        outer_polygon (Polygon): Shapely Polygon of the outer boundary
        gap_polygons (list): List of Shapely Polygons for gaps
        center_lat (float): Latitude to center the map
        center_lng (float): Longitude to center the map

    Returns:
        folium.Map object
    """
    m = folium.Map(location=[center_lat, center_lng], zoom_start=15)

    folium.GeoJson(
        mapping(outer_polygon),
        name="Outer Polygon",
        style_function=lambda feature: {
            'color': 'black',
            'weight': 2,
            'fill': False
        }
    ).add_to(m)

    for poly in tree_polygons:
        folium.GeoJson(
            mapping(poly),
            style_function=lambda feature: {
                'color': 'green',
                'weight': 1,
                'fillColor': 'green',
                'fillOpacity': 0.5
            }
        ).add_to(m)

    for poly in gap_polygons:
        folium.GeoJson(
            mapping(poly),
            style_function=lambda feature: {
                'color': 'red',
                'weight': 1,
                'fillColor': 'red',
                'fillOpacity': 0.5
            }
        ).add_to(m)

    return m
