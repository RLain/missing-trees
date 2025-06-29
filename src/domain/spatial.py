from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass
class TreePosition:
    lat: float
    lng: float
    confidence: str
    distance_to_nearest: float
    merged_from: Optional[int] = None


@dataclass
class OrchardAnalysisResult:
    missing_trees: List[TreePosition]
    summary: Dict[str, int]

