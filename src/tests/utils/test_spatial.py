import unittest
from shapely.geometry import Polygon
from utils.spatial import build_outer_polygon_from_survey, create_tree_polygons
from config import DEFAULT_PROJECTED_CRS, DEFAULT_GEOGRAPHIC_CRS

class TestBuildOuterPolygonFromSurvey(unittest.TestCase):
    def test_valid_polygon(self):
        survey = {
            "results": [
                {"polygon": "18.5,-33.9 18.6,-33.9 18.6,-33.8 18.5,-33.8 18.5,-33.9"}
            ]
        }

        expected_coords = [
            (18.5, -33.9),
            (18.6, -33.9),
            (18.6, -33.8),
            (18.5, -33.8),
            (18.5, -33.9),
        ]
        polygon = build_outer_polygon_from_survey(survey)
        self.assertIsInstance(polygon, Polygon)
        self.assertTrue(polygon.equals(Polygon(expected_coords)))

    def test_open_ring_raises_assert(self):
        survey = {
            "results": [{"polygon": "18.5,-33.9 18.6,-33.9 18.6,-33.8 18.5,-33.8"}]
        }
        with self.assertRaises(AssertionError):
            build_outer_polygon_from_survey(survey)

class TestCreateTreePolygons(unittest.TestCase):
    def test_valid_input(self):
        tree_data = [
            {"lat": -32.0, "lng": 18.0, "area": 3.14},
            {"lat": -32.1, "lng": 18.1, "area": 12.56},
        ]

        polygons = create_tree_polygons(tree_data)

        self.assertIsInstance(polygons, list)
        self.assertTrue(all(hasattr(p, "geom_type") for p in polygons))
        self.assertEqual(len(polygons), len(tree_data))

    def test_missing_key_raises_value_error(self):
        incomplete_data = [
            {"lat": -32.0, "lng": 18.0},
        ]
        with self.assertRaises(ValueError) as cm:
            create_tree_polygons(incomplete_data)
        self.assertIn("Missing one of", str(cm.exception))


if __name__ == "__main__":
    unittest.main()
