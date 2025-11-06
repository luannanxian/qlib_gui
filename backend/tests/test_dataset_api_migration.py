"""
Test Dataset API Migration

This test file verifies the dataset API migration from in-memory storage
to SQLAlchemy with comprehensive logging.

Run with:
    pytest tests/test_dataset_api_migration.py -v
    pytest tests/test_dataset_api_migration.py -v -s  # with logging output
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool
from typing import AsyncGenerator

from app.database.base import Base
from app.database import get_db
from app.main import app
from app.database.models.dataset import Dataset, DataSource, DatasetStatus


# Test database URL (using SQLite for tests)
TEST_DATABASE_URL = "mysql+aiomysql://remote:remote123456@192.168.3.46:3306/qlib_ui_test?charset=utf8mb4"


@pytest.fixture(scope="function")
async def test_db_engine():
    """Create test database engine"""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        poolclass=NullPool,
        echo=False
    )

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    # Drop all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest.fixture(scope="function")
async def test_db_session(test_db_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create test database session"""
    async_session_maker = async_sessionmaker(
        test_db_engine,
        class_=AsyncSession,
        expire_on_commit=False
    )

    async with async_session_maker() as session:
        yield session


@pytest.fixture(scope="function")
async def client(test_db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Create test client with test database"""

    async def override_get_db():
        yield test_db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


class TestDatasetAPIMigration:
    """Test suite for dataset API migration"""

    @pytest.mark.asyncio
    async def test_list_datasets_empty(self, client: AsyncClient):
        """Test listing datasets when database is empty"""
        response = await client.get("/api/datasets")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["items"] == []

    @pytest.mark.asyncio
    async def test_create_dataset(self, client: AsyncClient):
        """Test creating a new dataset"""
        dataset_data = {
            "name": "Test Stock Data",
            "source": "local",
            "file_path": "/data/test_stocks.csv",
            "extra_metadata": {"description": "Test dataset"}
        }

        response = await client.post("/api/datasets", json=dataset_data)

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Test Stock Data"
        assert data["source"] == "local"
        assert data["file_path"] == "/data/test_stocks.csv"
        assert data["status"] == "pending"
        assert data["row_count"] == 0
        assert "metadata" in data  # Aliased from extra_metadata
        assert data["metadata"]["description"] == "Test dataset"
        assert "id" in data
        assert "created_at" in data
        assert "updated_at" in data

    @pytest.mark.asyncio
    async def test_create_dataset_duplicate_name(self, client: AsyncClient):
        """Test creating dataset with duplicate name fails"""
        dataset_data = {
            "name": "Duplicate Test",
            "source": "local",
            "file_path": "/data/test1.csv"
        }

        # Create first dataset
        response1 = await client.post("/api/datasets", json=dataset_data)
        assert response1.status_code == 201

        # Try to create duplicate
        response2 = await client.post("/api/datasets", json=dataset_data)
        assert response2.status_code == 409
        assert "already exists" in response2.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_get_dataset_by_id(self, client: AsyncClient):
        """Test retrieving a dataset by ID"""
        # Create dataset first
        create_response = await client.post("/api/datasets", json={
            "name": "Test Dataset",
            "source": "qlib",
            "file_path": "/qlib/data"
        })
        dataset_id = create_response.json()["id"]

        # Get dataset by ID
        response = await client.get(f"/api/datasets/{dataset_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == dataset_id
        assert data["name"] == "Test Dataset"
        assert data["source"] == "qlib"

    @pytest.mark.asyncio
    async def test_get_dataset_not_found(self, client: AsyncClient):
        """Test getting non-existent dataset returns 404"""
        response = await client.get("/api/datasets/00000000-0000-0000-0000-000000000000")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_update_dataset(self, client: AsyncClient):
        """Test updating a dataset"""
        # Create dataset first
        create_response = await client.post("/api/datasets", json={
            "name": "Original Name",
            "source": "local",
            "file_path": "/data/original.csv"
        })
        dataset_id = create_response.json()["id"]

        # Update dataset
        update_data = {
            "name": "Updated Name",
            "status": "valid",
            "row_count": 1000,
            "columns": ["date", "symbol", "price"],
            "extra_metadata": {"updated": True}
        }
        response = await client.put(f"/api/datasets/{dataset_id}", json=update_data)

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == dataset_id
        assert data["name"] == "Updated Name"
        assert data["status"] == "valid"
        assert data["row_count"] == 1000
        assert data["columns"] == ["date", "symbol", "price"]
        assert data["metadata"]["updated"] is True

    @pytest.mark.asyncio
    async def test_update_dataset_partial(self, client: AsyncClient):
        """Test partial update of dataset"""
        # Create dataset
        create_response = await client.post("/api/datasets", json={
            "name": "Test Dataset",
            "source": "local",
            "file_path": "/data/test.csv"
        })
        dataset_id = create_response.json()["id"]

        # Partial update (only status)
        response = await client.put(
            f"/api/datasets/{dataset_id}",
            json={"status": "valid"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "valid"
        assert data["name"] == "Test Dataset"  # Unchanged

    @pytest.mark.asyncio
    async def test_update_dataset_not_found(self, client: AsyncClient):
        """Test updating non-existent dataset returns 404"""
        response = await client.put(
            "/api/datasets/00000000-0000-0000-0000-000000000000",
            json={"status": "valid"}
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_dataset_soft(self, client: AsyncClient):
        """Test soft deleting a dataset"""
        # Create dataset
        create_response = await client.post("/api/datasets", json={
            "name": "To Delete",
            "source": "local",
            "file_path": "/data/delete.csv"
        })
        dataset_id = create_response.json()["id"]

        # Soft delete
        response = await client.delete(f"/api/datasets/{dataset_id}")

        assert response.status_code == 204

        # Verify dataset is not in list
        list_response = await client.get("/api/datasets")
        assert list_response.status_code == 200
        assert list_response.json()["total"] == 0

    @pytest.mark.asyncio
    async def test_delete_dataset_hard(self, client: AsyncClient):
        """Test hard deleting a dataset"""
        # Create dataset
        create_response = await client.post("/api/datasets", json={
            "name": "To Hard Delete",
            "source": "local",
            "file_path": "/data/hard_delete.csv"
        })
        dataset_id = create_response.json()["id"]

        # Hard delete
        response = await client.delete(
            f"/api/datasets/{dataset_id}",
            params={"hard_delete": True}
        )

        assert response.status_code == 204

        # Verify dataset is gone
        get_response = await client.get(f"/api/datasets/{dataset_id}")
        assert get_response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_dataset_not_found(self, client: AsyncClient):
        """Test deleting non-existent dataset returns 404"""
        response = await client.delete("/api/datasets/00000000-0000-0000-0000-000000000000")

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_list_datasets_pagination(self, client: AsyncClient):
        """Test dataset pagination"""
        # Create multiple datasets
        for i in range(5):
            await client.post("/api/datasets", json={
                "name": f"Dataset {i}",
                "source": "local",
                "file_path": f"/data/test_{i}.csv"
            })

        # Test pagination
        response = await client.get("/api/datasets?skip=0&limit=2")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 5
        assert len(data["items"]) == 2

        # Test second page
        response2 = await client.get("/api/datasets?skip=2&limit=2")
        assert response2.status_code == 200
        data2 = response2.json()
        assert data2["total"] == 5
        assert len(data2["items"]) == 2

    @pytest.mark.asyncio
    async def test_list_datasets_filter_by_source(self, client: AsyncClient):
        """Test filtering datasets by source"""
        # Create datasets with different sources
        await client.post("/api/datasets", json={
            "name": "Local Dataset",
            "source": "local",
            "file_path": "/data/local.csv"
        })
        await client.post("/api/datasets", json={
            "name": "Qlib Dataset",
            "source": "qlib",
            "file_path": "/qlib/data"
        })

        # Filter by source
        response = await client.get("/api/datasets?source=local")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["items"][0]["source"] == "local"

    @pytest.mark.asyncio
    async def test_list_datasets_filter_by_status(self, client: AsyncClient):
        """Test filtering datasets by status"""
        # Create datasets with different statuses
        create_response = await client.post("/api/datasets", json={
            "name": "Valid Dataset",
            "source": "local",
            "file_path": "/data/valid.csv"
        })
        dataset_id = create_response.json()["id"]

        # Update status to valid
        await client.put(f"/api/datasets/{dataset_id}", json={"status": "valid"})

        # Create pending dataset
        await client.post("/api/datasets", json={
            "name": "Pending Dataset",
            "source": "local",
            "file_path": "/data/pending.csv"
        })

        # Filter by status
        response = await client.get("/api/datasets?status=valid")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["items"][0]["status"] == "valid"

    @pytest.mark.asyncio
    async def test_list_datasets_search(self, client: AsyncClient):
        """Test searching datasets by name"""
        # Create datasets
        await client.post("/api/datasets", json={
            "name": "Stock Market Data 2024",
            "source": "local",
            "file_path": "/data/stocks.csv"
        })
        await client.post("/api/datasets", json={
            "name": "Crypto Data",
            "source": "local",
            "file_path": "/data/crypto.csv"
        })

        # Search by name
        response = await client.get("/api/datasets?search=stock")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert "stock" in data["items"][0]["name"].lower()

    @pytest.mark.asyncio
    async def test_create_dataset_validation(self, client: AsyncClient):
        """Test dataset creation validation"""
        # Test with empty name
        response = await client.post("/api/datasets", json={
            "name": "   ",
            "source": "local",
            "file_path": "/data/test.csv"
        })
        assert response.status_code == 422  # Validation error

        # Test with missing required fields
        response2 = await client.post("/api/datasets", json={
            "name": "Test"
        })
        assert response2.status_code == 422

    @pytest.mark.asyncio
    async def test_correlation_id_tracking(self, client: AsyncClient):
        """Test correlation ID is properly tracked"""
        correlation_id = "test-correlation-123"

        response = await client.get(
            "/api/datasets",
            headers={"X-Correlation-ID": correlation_id}
        )

        assert response.status_code == 200
        # Correlation ID should be used in logging (check logs manually)


if __name__ == "__main__":
    # Run tests with pytest
    import sys
    pytest.main([__file__, "-v", "-s"] + sys.argv[1:])
