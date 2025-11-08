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


class TestAPIErrorHandling:
    """Test API error handling and edge cases."""

    @pytest.mark.asyncio
    async def test_create_config_with_invalid_capital(self, async_client: AsyncClient):
        """Test creating config with negative capital."""
        # ARRANGE
        config_data = {
            "strategy_id": "strategy_error",
            "dataset_id": "dataset_error",
            "start_date": "2023-01-01",
            "end_date": "2023-12-31",
            "initial_capital": "-100000.00",  # Negative capital
            "commission_rate": "0.001",
            "slippage": "0.0005"
        }

        # ACT
        response = await async_client.post("/api/backtest/config", json=config_data)

        # ASSERT
        assert response.status_code == 400
        assert "capital" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_update_config_not_found(self, async_client: AsyncClient):
        """Test updating non-existent configuration."""
        # ARRANGE
        update_data = {"initial_capital": "200000.00"}

        # ACT
        response = await async_client.put("/api/backtest/config/nonexistent_id", json=update_data)

        # ASSERT
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_config_with_commission_rate(self, async_client: AsyncClient):
        """Test updating configuration with commission_rate."""
        # ARRANGE - Create config first
        config_data = {
            "strategy_id": "strategy_commission",
            "dataset_id": "dataset_commission",
            "start_date": "2023-01-01",
            "end_date": "2023-12-31",
            "initial_capital": "100000.00",
            "commission_rate": "0.001",
            "slippage": "0.0005"
        }
        create_response = await async_client.post("/api/backtest/config", json=config_data)
        config_id = create_response.json()["id"]

        # ACT
        update_data = {
            "commission_rate": "0.002",
            "slippage": "0.001"
        }
        response = await async_client.put(f"/api/backtest/config/{config_id}", json=update_data)

        # ASSERT
        assert response.status_code == 200
        data = response.json()
        assert Decimal(data["commission_rate"]) == Decimal("0.002")
        assert Decimal(data["slippage"]) == Decimal("0.001")

    @pytest.mark.asyncio
    async def test_update_config_with_invalid_capital(self, async_client: AsyncClient):
        """Test updating config with invalid capital."""
        # ARRANGE - Create config first
        config_data = {
            "strategy_id": "strategy_update_error",
            "dataset_id": "dataset_update_error",
            "start_date": "2023-01-01",
            "end_date": "2023-12-31",
            "initial_capital": "100000.00",
            "commission_rate": "0.001",
            "slippage": "0.0005"
        }
        create_response = await async_client.post("/api/backtest/config", json=config_data)
        config_id = create_response.json()["id"]

        # ACT
        update_data = {"initial_capital": "-50000.00"}  # Negative capital
        response = await async_client.put(f"/api/backtest/config/{config_id}", json=update_data)

        # ASSERT
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_delete_config_not_found(self, async_client: AsyncClient):
        """Test deleting non-existent configuration."""
        # ACT
        response = await async_client.delete("/api/backtest/config/nonexistent_id")

        # ASSERT
        assert response.status_code == 404


class TestAPIDataConversion:
    """Test API data conversion and formatting."""

    @pytest.mark.asyncio
    async def test_create_config_date_conversion(self, async_client: AsyncClient):
        """Test date string to date object conversion in create."""
        # ARRANGE
        config_data = {
            "strategy_id": "strategy_date",
            "dataset_id": "dataset_date",
            "start_date": "2023-06-01",
            "end_date": "2023-09-30",
            "initial_capital": "150000.00",
            "commission_rate": "0.0015",
            "slippage": "0.0008"
        }

        # ACT
        response = await async_client.post("/api/backtest/config", json=config_data)

        # ASSERT
        assert response.status_code == 201
        data = response.json()
        assert data["start_date"] == "2023-06-01"
        assert data["end_date"] == "2023-09-30"

    @pytest.mark.asyncio
    async def test_get_config_response_format(self, async_client: AsyncClient):
        """Test get config returns properly formatted response."""
        # ARRANGE - Create config first
        config_data = {
            "strategy_id": "strategy_format",
            "dataset_id": "dataset_format",
            "start_date": "2023-03-01",
            "end_date": "2023-06-30",
            "initial_capital": "75000.50",
            "commission_rate": "0.0012",
            "slippage": "0.0006"
        }
        create_response = await async_client.post("/api/backtest/config", json=config_data)
        config_id = create_response.json()["id"]

        # ACT
        response = await async_client.get(f"/api/backtest/config/{config_id}")

        # ASSERT
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert "strategy_id" in data
        assert "dataset_id" in data
        assert "start_date" in data
        assert "end_date" in data
        assert "initial_capital" in data
        assert "commission_rate" in data
        assert "slippage" in data

    @pytest.mark.asyncio
    async def test_update_config_response_format(self, async_client: AsyncClient):
        """Test update config returns properly formatted response."""
        # ARRANGE - Create config first
        config_data = {
            "strategy_id": "strategy_update_format",
            "dataset_id": "dataset_update_format",
            "start_date": "2023-01-01",
            "end_date": "2023-12-31",
            "initial_capital": "100000.00",
            "commission_rate": "0.001",
            "slippage": "0.0005"
        }
        create_response = await async_client.post("/api/backtest/config", json=config_data)
        config_id = create_response.json()["id"]

        # ACT
        update_data = {
            "initial_capital": "250000.75",
            "commission_rate": "0.0025",
            "slippage": "0.0012"
        }
        response = await async_client.put(f"/api/backtest/config/{config_id}", json=update_data)

        # ASSERT
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == config_id
        assert Decimal(data["initial_capital"]) == Decimal("250000.75")
        assert Decimal(data["commission_rate"]) == Decimal("0.0025")
        assert Decimal(data["slippage"]) == Decimal("0.0012")
        assert data["start_date"] == "2023-01-01"
        assert data["end_date"] == "2023-12-31"

    @pytest.mark.asyncio
    async def test_start_backtest_response_format(self, async_client: AsyncClient):
        """Test start backtest returns properly formatted response."""
        # ARRANGE - Create config first
        config_data = {
            "strategy_id": "strategy_start_format",
            "dataset_id": "dataset_start_format",
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
        assert "id" in data
        assert "config_id" in data
        assert "status" in data
        assert "total_return" in data
        assert "annual_return" in data
        assert "sharpe_ratio" in data
        assert "max_drawdown" in data
        assert "win_rate" in data
        # Verify Decimal fields are converted to strings
        assert isinstance(data["total_return"], str)
        assert isinstance(data["annual_return"], str)
        assert isinstance(data["sharpe_ratio"], str)

    @pytest.mark.asyncio
    async def test_delete_config_response_message(self, async_client: AsyncClient):
        """Test delete config returns success message."""
        # ARRANGE - Create config first
        config_data = {
            "strategy_id": "strategy_delete_msg",
            "dataset_id": "dataset_delete_msg",
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
        data = response.json()
        assert "message" in data
        assert "successfully" in data["message"].lower()
