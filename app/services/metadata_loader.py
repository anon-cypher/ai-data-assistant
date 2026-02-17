import json
from app.utils.config import TABLE_METADATA_PATH


def load_table_metadata():
    """Load and return table metadata JSON from configured path.

    Args:
     - None

    Return:
     - The parsed JSON object (typically a list/dict) representing table metadata.
    """
    with open(TABLE_METADATA_PATH) as f:
        return json.load(f)
