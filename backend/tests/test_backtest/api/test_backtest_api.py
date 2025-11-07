"""
TDD Tests for Backtest API Endpoints

Test coverage for:
- POST /api/backtest/config - Create configuration
- GET /api/backtest/config/{id} - Get configuration
- PUT /api/backtest/config/{id} - Update configuration
- DELETE /api/backtest/config/{id} - Delete configuration
- POST /api/backtest/{id}/start - Start backtest
- GET /api/backtest/{id}/status - Get status
"""

import pytest
from httpx import AsyncClient
from datetime import date
from decimal import Decimal


class TestConfigEndpoints:
    """Test configuration CRUD endpoints."""

    @pytest.mark.asyncio
    async def test_create_config_success(self, async_client: AsyncClient):
        """Test creating a backtest configuration."""
        # ARRANGE
        config_data = {
            "strategy_id": "strategy_001",
            "dataset_id": "dataset_001",
            "start_date": "2023-01-01",
            "end_date": "2023-12-31",
            "initial_capital": "100000.00",
            "commission_rate": "0.001",
            "slippage": "0.0005"
        }

        # ACT
        response = await async_client.post("/api/backtest/config", json=config_data)

        # ASSERT
        assert response.status_code == 201
        data = response.json()
        assert data["strategy_id"] == "strategy_001"
        assert data["dataset_id"] == "dataset_001"
        assert "id" in data

    @pytest.mark.asyncio
    async def test_create_config_invalid_date_range(self, async_client: AsyncClient):
        """Test creating config with invalid date range."""
        # ARRANGE
        config_data = {
            "strategy_id": "strategy_001",
            "dataset_id": "dataset_001",
            "start_date": "2023-12-31",
            "end_date": "2023-01-01",
            "initial_capital": "100000.00",
            "commission_rate": "0.001",
            "slippage": "0.0005"
        }

        # ACT
        response = await async_client.post("/api/backtest/config", json=config_data)

        # ASSERT
        assert response.status_code == 400
        assert "start_date" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_get_config_success(self, async_client: AsyncClient):
        """Test retrieving a configuration."""
        # ARRANGE - Create config first
        config_data = {
            "strategy_id": "strategy_002",
            "dataset_id": "dataset_002",
            "start_date": "2023-01-01",
            "end_date": "2023-12-31",
            "initial_capital": "100000.00",
            "commission_rate": "0.001",
            "slippage": "0.0005"
        }
        create_response = await async_client.post("/api/backtest/config", json=config_data)
        config_id = create_response.json()["id"]

        # ACT
        response = await async_client.get(f"/api/backtest/config/{config_id}")

        # ASSERT
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == config_id
        assert data["strategy_id"] == "strategy_002"

    @pytest.mark.asyncio
    async def test_get_config_not_found(self, async_client: AsyncClient):
        """Test retrieving non-existent configuration."""
        # ACT
        response = await async_client.get("/api/backtest/config/nonexistent_id")

        # ASSERT
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_config_success(self, async_client: AsyncClient):
        """Test updating a configuration."""
        # ARRANGE - Create config first
        config_data = {
            "strategy_id": "strategy_003",
            "dataset_id": "dataset_003",
            "start_date": "2023-01-01",
            "end_date": "2023-12-31",
            "initial_capital": "100000.00",
            "commission_rate": "0.001",
            "slippage": "0.0005"
        }
        create_response = await async_client.post("/api/backtest/config", json=config_data)
        config_id = create_response.json()["id"]

        # ACT
        update_data = {"initial_capital": "200000.00"}
        response = await async_client.put(f"/api/backtest/config/{config_id}", json=update_data)

        # ASSERT
        assert response.status_code == 200
        data = response.json()
        assert data["initial_capital"] == "200000.00"

    @pytest.mark.asyncio
    async def test_delete_config_success(self, async_client: AsyncClient):
        """Test deleting a configuration."""
        # ARRANGE - Create config first
        config_data = {
            "strategy_id": "strategy_004",
            "dataset_id": "dataset_004",
            "start_date": "2023-01-01",
            "end_date": "2023-12-31",
            "initial_capital": "100000.00",
            "commission_rate": "0.001",
            "slippage": "0.0005"
        }
        create_response = await async_client.post("/api/backtest/config", json=config_data)
        config_id = create_response.json()["id"]

        # ACT
        response = await async_client.delete(f"/api/backtest/config/{config_id}")

        # ASSERT
        assert response.status_code == 200


class TestExecutionEndpoints:
    """Test backtest execution endpoints."""

    @pytest.mark.asyncio
    async def test_start_backtest_success(self, async_client: AsyncClient):
        """Test starting a backtest."""
        # ARRANGE - Create config first
        config_data = {
            "strategy_id": "strategy_005",
            "dataset_id": "dataset_005",
            "start_date": "2023-01-01",
            "end_date": "2023-12-31",
            "initial_capital": "100000.00",
            "commission_rate": "0.001",
            "slippage": "0.0005"
        }
        create_response = await async_client.post("/api/backtest/config", json=config_data)
        config_id = create_response.json()["id"]

        # ACT
        response = await async_client.post(f"/api/backtest/{config_id}/start")

        # ASSERT
        assert response.status_code == 201
        data = response.json()
        assert data["config_id"] == config_id
        assert data["status"] == "PENDING"
        assert "id" in data

    @pytest.mark.asyncio
    async def test_start_backtest_invalid_config(self, async_client: AsyncClient):
        """Test starting backtest with invalid config ID."""
        # ACT
        response = await async_client.post("/api/backtest/nonexistent_id/start")

        # ASSERT
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_backtest_status_success(self, async_client: AsyncClient):
        """Test getting backtest status."""
        # ARRANGE - Create config and start backtest
        config_data = {
            "strategy_id": "strategy_006",
            "dataset_id": "dataset_006",
            "start_date": "2023-01-01",
            "end_date": "2023-12-31",
            "initial_capital": "100000.00",
            "commission_rate": "0.001",
            "slippage": "0.0005"
        }
        create_response = await async_client.post("/api/backtest/config", json=config_data)
        config_id = create_response.json()["id"]
        start_response = await async_client.post(f"/api/backtest/{config_id}/start")
        result_id = start_response.json()["id"]

        # ACT
        response = await async_client.get(f"/api/backtest/{result_id}/status")

        # ASSERT
        assert response.status_code == 200
        data = response.json()
        assert data["status"] in ["PENDING", "RUNNING", "COMPLETED", "FAILED"]

    @pytest.mark.asyncio
    async def test_get_backtest_status_not_found(self, async_client: AsyncClient):
        """Test getting status for non-existent backtest."""
        # ACT
        response = await async_client.get("/api/backtest/nonexistent_id/status")

        # ASSERT
        assert response.status_code == 404
