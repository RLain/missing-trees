import folium
from shapely.geometry import Point
import geopandas as gpd
from typing import List, Dict, Optional, Union


def create_orchard_map(
    tree_polygons: List,
    outer_polygon,
    labeled_points: Optional[List[Dict]] = None,
    tree_points: Optional[List[Union[Point, tuple]]] = None,
    missing_points: Optional[List[Dict]] = None,
    expected_grid: Optional[List[Dict]] = None,  # New: show expected positions
    matched_trees: Optional[List[Dict]] = None,  # New: show matching accuracy
) -> folium.Map:
    """
    Create comprehensive orchard visualization with missing tree detection.
    """

    centroid = outer_polygon.centroid
    folium_map = folium.Map(
        location=[centroid.y, centroid.x],
        zoom_start=18,  # Increased zoom for tree-level detail
        tiles="Esri.WorldImagery",
    )

    # Outer polygon boundary
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

    # Tree crown polygons
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

    # Expected grid positions (helpful for validation)
    if expected_grid:
        grid_group = folium.FeatureGroup(name="Expected Grid", show=False)
        for pos in expected_grid:
            folium.CircleMarker(
                location=[pos["lat"], pos["lng"]],
                radius=2,
                color="gray",
                fill=True,
                fill_opacity=0.3,
                weight=1,
                tooltip=f"Expected: R{pos.get('row', '?')}.C{pos.get('col', '?')}",
            ).add_to(grid_group)
        grid_group.add_to(folium_map)

    # Existing tree points with accuracy indicators
    if tree_points:
        tree_group = folium.FeatureGroup(name="Existing Trees")
        for i, pt in enumerate(tree_points):
            lat, lng = (pt.y, pt.x) if isinstance(pt, Point) else pt

            # Color code by matching accuracy if available
            color = "green"
            tooltip_text = "Existing Tree"

            if matched_trees and i < len(matched_trees):
                match_info = matched_trees[i]
                distance = match_info.get("distance_from_expected", 0)
                if distance > 2.0:
                    color = "pink"  # Poor alignment
                    tooltip_text = f"Tree (±{distance:.1f}m from expected)"
                else:
                    tooltip_text = f"Tree (±{distance:.1f}m from expected)"

            folium.CircleMarker(
                location=[lat, lng],
                radius=4,
                color=color,
                fill=True,
                fill_opacity=0.8,
                weight=2,
                tooltip=tooltip_text,
            ).add_to(tree_group)
        tree_group.add_to(folium_map)

    # Tree labels with improved styling
    if labeled_points:
        label_group = folium.FeatureGroup(name="Tree Labels")
        for pt in labeled_points:
            lat = pt["lat"]
            lng = pt["lng"]
            label = pt["label"]

            folium.Marker(
                location=[lat, lng],
                icon=folium.DivIcon(
                    html=f"""
                    <div style="
                        font-size: 4pt; 
                        color: white; 
                        padding: 2px 4px; 
                        border-radius: 3px;
                        font-weight: bold;
                        text-align: center;
                        min-width: 20px;
                    ">{label}</div>
                    """,
                    icon_size=(20, 15),
                    icon_anchor=(10, 7),
                ),
            ).add_to(label_group)
        label_group.add_to(folium_map)

    # Missing trees with priority indicators
    # if missing_points:
    #     missing_group = folium.FeatureGroup(name="Missing Trees")
    #     for i, pt in enumerate(missing_points):
    #         lat = pt["lat"]
    #         lng = pt["lng"]
    #         confidence = pt.get("confidence", "medium")

    #         # Color by confidence level
    #         color_map = {
    #             "high": "red",
    #             "medium": "orange",
    #             "low": "yellow"
    #         }
    #         color = color_map.get(confidence, "red")

    #         folium.CircleMarker(
    #             location=[lat, lng],
    #             radius=6,
    #             color=color,
    #             fill=True,
    #             fill_opacity=0.9,
    #             weight=2,
    #             tooltip=f"Missing Tree #{i+1} (Confidence: {confidence})"
    #         ).add_to(missing_group)
    #     missing_group.add_to(folium_map)

    # Add layer control
    folium.LayerControl().add_to(folium_map)

    # Add custom legend
    legend_html = """
    <div style="position: fixed; 
                bottom: 50px; left: 50px; width: 200px; height: 200px; 
                background-color: white; border:2px solid grey; z-index:9999; 
                font-size:14px; padding: 10px">
    <h4>Legend</h4>
    <p><i class="fa fa-circle" style="color:green"></i> Existing Trees</p>
    <p><i class="fa fa-circle" style="color:pink"></i> Existing Trees (poor alignment)</p>
    <p><i class="fa fa-circle" style="color:red"></i> Missing Trees (High)</p>
    <p><i class="fa fa-circle" style="color:orange"></i> Missing Trees (Medium)</p>
    <p><i class="fa fa-circle" style="color:gray"></i> Expected Grid</p>
    </div>
    """
    folium_map.get_root().html.add_child(folium.Element(legend_html))

    return folium_map
