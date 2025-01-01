from typing import Generator

import mongomock
import pytest

from lm_saes.config import SAEConfig
from lm_saes.database import MongoClient, SAERecord


@pytest.fixture
def mongo_client() -> MongoClient:
    """
    Creates a MongoClient instance with an in-memory MongoDB.

    Returns:
        MongoClient: A configured MongoClient instance for testing
    """
    with mongomock.patch(servers=(("fake", 27017),)):
        client = MongoClient("mongodb://fake", "test_db")
        yield client
        # Clear all collections after each test
        client.db.drop_collection("sae")
        client.db.drop_collection("analysis")
        client.db.drop_collection("feature")


def test_create_and_get_sae(mongo_client: MongoClient) -> None:
    """Test creating and retrieving an SAE record."""
    # Arrange
    name = "test_sae"
    series = "test_series"
    cfg = SAEConfig(hook_point_in="test_hook_point_in", d_sae=10, d_model=10, expansion_factor=1)

    # Act
    mongo_client.create_sae(name, series, cfg)
    result = mongo_client.get_sae(name, series)

    # Assert
    assert isinstance(result, SAERecord)
    assert result.name == name
    assert result.series == series
    assert result.cfg.d_sae == cfg.d_sae


def test_list_saes(mongo_client: MongoClient) -> None:
    """Test listing SAE records."""
    # Arrange
    cfg = SAEConfig(hook_point_in="test_hook_point_in", d_sae=10, d_model=10, expansion_factor=1)
    print(mongo_client.sae_collection.find_one())
    mongo_client.create_sae("sae1", "series1", cfg)
    mongo_client.create_sae("sae2", "series1", cfg)
    mongo_client.create_sae("sae3", "series2", cfg)

    # Act & Assert
    assert set(mongo_client.list_saes()) == {"sae1", "sae2", "sae3"}
    assert set(mongo_client.list_saes("series1")) == {"sae1", "sae2"}
    assert set(mongo_client.list_saes("series2")) == {"sae3"}


def test_remove_sae(mongo_client: MongoClient) -> None:
    """Test removing an SAE record."""
    # Arrange
    name = "test_sae"
    series = "test_series"
    cfg = SAEConfig(hook_point_in="test_hook_point_in", d_sae=10, d_model=10, expansion_factor=1)
    mongo_client.create_sae(name, series, cfg)

    # Act
    mongo_client.remove_sae(name, series)

    # Assert
    assert mongo_client.get_sae(name, series) is None
    assert mongo_client.list_saes(series) == []


def test_create_and_get_analysis(mongo_client: MongoClient) -> None:
    """Test creating and retrieving analysis records."""
    # Arrange
    cfg = SAEConfig(hook_point_in="test_hook_point_in", d_sae=10, d_model=10, expansion_factor=1)
    mongo_client.create_sae("test_sae", "test_series", cfg)

    # Act
    mongo_client.create_analysis("test_analysis", "test_sae", "test_series")
    analyses = mongo_client.list_analyses("test_sae", "test_series")

    # Assert
    assert analyses == ["test_analysis"]


def test_get_nonexistent_sae(mongo_client: MongoClient) -> None:
    """Test retrieving a non-existent SAE record."""
    assert mongo_client.get_sae("nonexistent", "series") is None


def test_get_feature(mongo_client: MongoClient) -> None:
    """Test retrieving feature records."""
    # Arrange
    cfg = SAEConfig(hook_point_in="test_hook_point_in", d_sae=2, d_model=2, expansion_factor=1)
    mongo_client.create_sae("test_sae", "test_series", cfg)

    # Act
    feature = mongo_client.get_feature("test_sae", "test_series", 0)

    # Assert
    assert feature is not None
    assert feature.sae_name == "test_sae"
    assert feature.sae_series == "test_series"
    assert feature.index == 0
