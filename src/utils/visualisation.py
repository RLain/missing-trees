import folium
from shapely.geometry import Point

# TODO: Type the properties 
def create_map(tree_polygons, outer_polygon, labeled_points=None, tree_points=None, missing_points=None):
    print("labeled_points sample:", labeled_points[0], type(labeled_points[0]))
    print("tree_points sample:", tree_points[0], type(tree_points[0]))
    print("missing_points sample:", missing_points[0], type(missing_points[0]))

    centroid = outer_polygon.centroid
    folium_map = folium.Map(location=[centroid.y, centroid.x], zoom_start=16, tiles='Esri.WorldImagery')

    folium.GeoJson(
        outer_polygon,
        name="Outer Polygon",
        style_function=lambda x: {"color": "blue", "fill": False, "weight": 2}
    ).add_to(folium_map)
    
    for tree_area in tree_polygons:
        folium.GeoJson(
            tree_area,
            name="Treee area",
            style_function=lambda x: {"color": "dark-green", "weight": 1}
        ).add_to(folium_map)
        
    if labeled_points:
        label_group = folium.FeatureGroup(name="Tree Labels")
        for pt in labeled_points:
            lat = pt["lat"]
            lng = pt["lng"]
            label = pt["label"]
            folium.Marker(
                location=[lat, lng],
                icon=folium.DivIcon(
                    html=f"""<div style="font-size: 5pt; color: white; padding: 2px; border-radius: 3px;">{label}</div>"""
                ),
            ).add_to(label_group)
        label_group.add_to(folium_map)

    if tree_points:
        tree_group = folium.FeatureGroup(name="Tree Points")
        for pt in tree_points:
            lat, lng = (pt.y, pt.x) if isinstance(pt, Point) else pt
            folium.CircleMarker(
                location=[lat, lng],
                radius=3,
                color="green",
                fill=True,
                fill_opacity=0.7,
                tooltip="Existing Tree"
            ).add_to(tree_group)
        tree_group.add_to(folium_map)

    if missing_points:
        missing_group = folium.FeatureGroup(name="Missing Trees")
        for pt in missing_points:
            lat = pt["lat"]
            lng = pt["lng"]
            folium.CircleMarker(
                location=[lat, lng],
                radius=5,
                color="red",
                fill=True,
                fill_opacity=0.8,
                tooltip="Missing Tree"
            ).add_to(missing_group)
        missing_group.add_to(folium_map)

    folium.LayerControl().add_to(folium_map)

    return folium_map
