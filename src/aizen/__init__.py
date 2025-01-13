import json
import os

def _load_json(filename):
    """Load a JSON file from the aizen root directory."""
    path = os.path.join(os.path.dirname(__file__), filename)
    with open(path, 'r') as f:
        return json.load(f)

# Load function definitions from root aizen directory
FUNCTION_DEFINITIONS = _load_json('function_definitions.json')

__all__ = [
    'FUNCTION_DEFINITIONS'
]