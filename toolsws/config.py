from pathlib import Path
from typing import Any, Dict

import yaml

WEBSERVICE_CONFIG_PATH = Path("/etc/toolforge/webservice.yaml")


def load_config() -> Dict[str, Any]:
    if WEBSERVICE_CONFIG_PATH.exists():
        return yaml.safe_load(WEBSERVICE_CONFIG_PATH.read_text())
    return {}
