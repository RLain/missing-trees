
from typing import Dict, List

def validate_tree_data(tree_data: List[Dict]) -> None:
    if not tree_data:
        raise ValueError("Tree data cannot be empty")
    
    required_keys = {"lat", "lng", "area"}
    invalid_trees = []
    
    for i, tree in enumerate(tree_data):
        if not required_keys.issubset(tree.keys()):
            invalid_trees.append(i)
        elif not all(isinstance(tree[key], (int, float)) for key in required_keys):
            invalid_trees.append(i)
        elif tree["area"] <= 0:
            invalid_trees.append(i)
    
    if invalid_trees:
        raise ValueError(f"Invalid tree data at indices: {invalid_trees}")