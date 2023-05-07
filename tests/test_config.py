from pathlib import Path
from typing import Any, Dict

import pytest
import yaml

from toolsws import config


@pytest.fixture
def fake_config_file_location(monkeypatch, tmp_path):
    config_file = tmp_path / "webservice.yaml"
    monkeypatch.setattr(config, "WEBSERVICE_CONFIG_PATH", config_file)
    yield config_file


@pytest.fixture
def fake_config_file_with_data(fake_config_file_location: Path):
    data = {"foo": "bar"}
    fake_config_file_location.write_text(yaml.safe_dump(data))
    yield data


def test_load_config_default(fake_config_file_location):
    assert config.load_config() == {}


def test_load_config_with_data(fake_config_file_with_data: Dict[str, Any]):
    assert config.load_config() == fake_config_file_with_data
