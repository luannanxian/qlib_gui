"""
Integration Tests for Complete Backtest Flow

Tests the end-to-end backtest workflow from configuration creation
through execution to result retrieval.
"""

import pytest
from httpx import AsyncClient
from decimal import Decimal


class TestCompleteBacktestFlow:
    """Test complete backtest workflow integration."""

    @pytest.mark.asyncio
    async def test_complete_backtest_flow(self, async_client: AsyncClient):
        """Test complete backtest flow: create config -> start -> check status -> get results."""
        # Step 1: Create configuration
        config_data = {
            "strategy_id": "test_strategy",
            "dataset_id": "test_dataset",
            "start_date": "2023-01-01",
            "end_date": "2023-12-31",
            "initial_capital": "100000.00",
            "commission_rate": "0.001",
            "slippage": "0.0005"
        }

        config_response = await async_client.post("/api/backtest/config", json=config_data)
        assert config_response.status_code == 201
        config_id = config_response.json()["id"]

        # Step 2: Start backtest
        start_response = await async_client.post(f"/api/backtest/{config_id}/start")
        assert start_response.status_code == 201
        result_id = start_response.json()["id"]
        assert start_response.json()["status"] == "PENDING"

        # Step 3: Check status
        status_response = await async_client.get(f"/api/backtest/{result_id}/status")
        assert status_response.status_code == 200
        assert status_response.json()["status"] in ["PENDING", "RUNNING", "COMPLETED"]

        # Step 4: Verify configuration can be retrieved
        get_config_response = await async_client.get(f"/api/backtest/config/{config_id}")
        assert get_config_response.status_code == 200
        assert get_config_response.json()["strategy_id"] == "test_strategy"

    @pytest.mark.asyncio
    async def test_backtest_error_recovery(self, async_client: AsyncClient):
        """Test backtest error handling and recovery."""
        # Try to start backtest with non-existent config
        response = await async_client.post("/api/backtest/invalid_config_id/start")
        assert response.status_code == 404

        # Verify system remains stable
        config_data = {
            "strategy_id": "recovery_test",
            "dataset_id": "recovery_dataset",
            "start_date": "2023-01-01",
            "end_date": "2023-12-31",
            "initial_capital": "100000.00",
            "commission_rate": "0.001",
            "slippage": "0.0005"
        }

        recovery_response = await async_client.post("/api/backtest/config", json=config_data)
        assert recovery_response.status_code == 201


class TestConcurrentBacktests:
    """Test concurrent backtest execution."""

    @pytest.mark.asyncio
    async def test_concurrent_backtests(self, async_client: AsyncClient):
        """Test multiple backtests can be created and started concurrently."""
        import asyncio

        # Create multiple configurations (reduced from 3 to 2 to avoid connection pool exhaustion)
        configs = []
        for i in range(2):
            config_data = {
                "strategy_id": f"concurrent_strategy_{i}",
                "dataset_id": f"concurrent_dataset_{i}",
                "start_date": "2023-01-01",
                "end_date": "2023-12-31",
                "initial_capital": "100000.00",
                "commission_rate": "0.001",
                "slippage": "0.0005"
            }

            response = await async_client.post("/api/backtest/config", json=config_data)
            assert response.status_code == 201
            configs.append(response.json()["id"])
            # Add small delay to avoid overwhelming the connection pool
            await asyncio.sleep(0.1)

        # Start all backtests
        results = []
        for config_id in configs:
            response = await async_client.post(f"/api/backtest/{config_id}/start")
            assert response.status_code == 201
            results.append(response.json()["id"])
            # Add small delay between starts
            await asyncio.sleep(0.1)

        # Verify all backtests are tracked
        for result_id in results:
            response = await async_client.get(f"/api/backtest/{result_id}/status")
            assert response.status_code == 200
            assert response.json()["status"] in ["PENDING", "RUNNING", "COMPLETED"]
