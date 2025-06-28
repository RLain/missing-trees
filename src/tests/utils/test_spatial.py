import unittest
from shapely.geometry import Polygon
from utils.spatial import build_outer_polygon_from_survey


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


if __name__ == "__main__":
    unittest.main()
