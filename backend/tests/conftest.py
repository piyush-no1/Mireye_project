import os
import json
import pytest

@pytest.fixture
def fixtures_dir():
    return os.path.join(os.path.dirname(__file__), "fixtures")

@pytest.fixture
def sample_geocode(fixtures_dir):
    with open(os.path.join(fixtures_dir, "mireye_geocode_sample.json"), "r") as f:
        return json.load(f)

@pytest.fixture
def sample_nldi(fixtures_dir):
    with open(os.path.join(fixtures_dir, "usgs_nldi_sample.json"), "r") as f:
        return json.load(f)

@pytest.fixture
def sample_nwis(fixtures_dir):
    with open(os.path.join(fixtures_dir, "usgs_nwis_sample.json"), "r") as f:
        return json.load(f)

@pytest.fixture
def sample_wqp(fixtures_dir):
    with open(os.path.join(fixtures_dir, "epa_wqp_sample.json"), "r") as f:
        return json.load(f)

@pytest.fixture
def sample_attains(fixtures_dir):
    with open(os.path.join(fixtures_dir, "epa_attains_sample.json"), "r") as f:
        return json.load(f)

@pytest.fixture
def sample_echo(fixtures_dir):
    with open(os.path.join(fixtures_dir, "epa_echo_sample.json"), "r") as f:
        return json.load(f)

@pytest.fixture
def sample_land_risk(fixtures_dir):
    with open(os.path.join(fixtures_dir, "mireye_land_risk_sample.json"), "r") as f:
        return json.load(f)
