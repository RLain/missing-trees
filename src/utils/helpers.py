from src.domain import spatial
import numpy as np


def convert_result_to_analysis(result_dict: dict) -> spatial.OrchardAnalysisResult:
    def clean_value(value):
        if isinstance(value, (np.float32, np.float64)):
            return float(value)
        elif isinstance(value, (np.int32, np.int64)):
            return int(value)
        return value

    def clean_tree(tree: dict) -> spatial.TreePosition:
        return spatial.TreePosition(
            lat=clean_value(tree["lat"]),
            lng=clean_value(tree["lng"]),
            confidence=tree["confidence"],
            distance_to_nearest=clean_value(tree["distance_to_nearest"]),
            merged_from=clean_value(tree.get("merged_from"))
        )

    missing_trees_raw = result_dict.get("missing_coords", [])
    missing_trees = [clean_tree(tree) for tree in missing_trees_raw]

    summary = {
        k: clean_value(v)
        for k, v in result_dict.get("summary", {}).items()
    }

    return spatial.OrchardAnalysisResult(
        missing_trees=missing_trees,
        summary=summary
    )


def orchard_result_to_dict(result: spatial.OrchardAnalysisResult) -> dict:
    return {
        "missing_trees": [
            {
                "lat": tree.lat,
                "lng": tree.lng,
                "confidence": tree.confidence,
                "distance_to_nearest": tree.distance_to_nearest,
                "merged_from": tree.merged_from,
            }
            for tree in result.missing_trees
        ],
        "summary": result.summary
    }

