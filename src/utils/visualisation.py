import folium

def create_map(tree_polygons, outer_polygon, gap_polygons):
    centroid = outer_polygon.centroid
    folium_map = folium.Map(location=[centroid.y, centroid.x], zoom_start=16, tiles='Esri.WorldImagery')

    folium.GeoJson(
        outer_polygon,
        name="Outer Polygon",
        style_function=lambda x: {
            "color": "blue", "fill": False, "weight": 2
        }
    ).add_to(folium_map)
    
    print("create_map_tree_polygons", tree_polygons)

    for poly in tree_polygons:
        folium.GeoJson(
            poly,
            name="Tree",
            style_function=lambda x: {
                "color": "green", "fillColor": "green", "fillOpacity": 0.5, "weight": 1
            }
        ).add_to(folium_map)

    for gap in gap_polygons:
        folium.GeoJson(
            gap,
            name="Gap",
            style_function=lambda x: {
                "color": "red", "fillColor": "red", "fillOpacity": 0.5, "weight": 1
            }
        ).add_to(folium_map)

    folium.LayerControl().add_to(folium_map)
    folium.Marker([centroid.y, centroid.x], tooltip="Map center").add_to(folium_map)

    return folium_map
