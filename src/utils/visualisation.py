import folium
from typing import List, Dict, Optional
from shapely.geometry import Polygon


def create_orchard_map(
    tree_polygons: List,
    outer_polygon: Polygon,
    inner_boundary: Polygon,
    missing_points: Optional[List[Dict]] = None,
) -> folium.Map:
    centroid = outer_polygon.centroid
    folium_map = folium.Map(
        location=[centroid.y, centroid.x],
        zoom_start=18,
        tiles="Esri.WorldImagery",
    )

    folium.GeoJson(
        outer_polygon,
        name="Orchard Boundary",
        style_function=lambda x: {
            "color": "blue",
            "fill": False,
            "weight": 3,
            "opacity": 0.8,
        },
    ).add_to(folium_map)

    folium.GeoJson(
        inner_boundary,
        name="Inner Boundary",
        style_function=lambda x: {
            "color": "pink",
            "fill": False,
            "weight": 3,
            "opacity": 0.8,
        },
    ).add_to(folium_map)

    if tree_polygons:
        tree_polygon_group = folium.FeatureGroup(name="Tree Crowns")
        for i, tree_area in enumerate(tree_polygons):
            folium.GeoJson(
                tree_area,
                style_function=lambda x: {
                    "color": "darkgreen",
                    "weight": 1,
                    "fillColor": "green",
                    "fillOpacity": 0.3,
                },
                tooltip=f"Tree Crown {i+1}",
            ).add_to(tree_polygon_group)
        tree_polygon_group.add_to(folium_map)

    if missing_points:
        missing_group = folium.FeatureGroup(name="Missing Trees")
        for i, pt in enumerate(missing_points):
            lat = pt["lat"]
            lng = pt["lng"]
            confidence = pt.get("confidence", "medium")

            color_map = {"high": "red", "medium": "orange", "low": "yellow"}
            color = color_map.get(confidence, "red")

            folium.CircleMarker(
                location=[lat, lng],
                radius=6,
                color=color,
                fill=True,
                fill_opacity=0.9,
                weight=2,
                tooltip=f"Missing Tree #{i+1} (Confidence: {confidence})",
            ).add_to(missing_group)
        missing_group.add_to(folium_map)

    folium.LayerControl().add_to(folium_map)

    legend_html = """
    <div style="position: fixed;
                bottom: 50px; left: 50px; width: 200px; height: 160px;
                background-color: white; border:2px solid grey; z-index:9999;
                font-size:14px; padding: 10px">
    <h4>Legend</h4>
    <p><i class="fa fa-circle" style="color:blue"></i> Outer boundary</p>
    <p><i class="fa fa-circle" style="color:green"></i> Existing Trees</p>
    <p><i class="fa fa-circle" style="color:pink"></i> Inner boundary</p>
    <p><i class="fa fa-circle" style="color:red"></i> Missing Trees (High)</p>
    </div>
    """
    folium_map.get_root().html.add_child(folium.Element(legend_html))

    return folium_map