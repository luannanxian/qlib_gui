"""
TDD Tests for Custom Factor API Endpoints

Comprehensive test suite covering:
- POST /api/custom-factors (create factor)
- GET /api/custom-factors (list user factors)
- GET /api/custom-factors/{factor_id} (get factor detail)
- PUT /api/custom-factors/{factor_id} (update factor)
- DELETE /api/custom-factors/{factor_id} (delete factor)
- POST /api/custom-factors/{factor_id}/publish (publish factor)
- POST /api/custom-factors/{factor_id}/clone (clone factor)

Following TDD best practices:
- AAA pattern (Arrange-Act-Assert)
- Test HTTP status codes and response structure
- Test request body validation
- Test authorization checks
- Test error handling
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.indicator import (
    CustomFactor, IndicatorComponent, FactorStatus
)


@pytest.mark.asyncio
class TestCreateCustomFactor:
    """Test POST /api/custom-factors endpoint."""

    async def test_create_factor_success(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession
    ):
        """Test creating a custom factor successfully."""
        # ARRANGE
        factor_data = {
            "factor_name": "测试动量因子",
            "formula": "(close - open) / open",
            "formula_language": "qlib_alpha",
            "description": "基于开盘和收盘价的动量因子"
        }

        # ACT
        response = await async_client.post(
            "/api/custom-factors",
            json=factor_data
        )

        # ASSERT
        assert response.status_code == 201
        data = response.json()
        assert data["factor_name"] == factor_data["factor_name"]
        assert data["formula"] == factor_data["formula"]
        assert data["formula_language"] == factor_data["formula_language"]
        assert data["description"] == factor_data["description"]
        assert data["status"] == FactorStatus.DRAFT.value
        assert data["is_public"] is False
        assert data["user_id"] == "user123"  # Mock user ID
        assert "id" in data
        assert "created_at" in data
        assert "updated_at" in data

    async def test_create_factor_with_optional_fields(
        self,
        async_client: AsyncClient,
        sample_indicator: IndicatorComponent
    ):
        """Test creating a custom factor with optional fields."""
        # ARRANGE
        factor_data = {
            "factor_name": "完整配置因子",
            "formula": "close / open - 1",
            "formula_language": "qlib_alpha",
            "description": "包含所有可选字段的因子",
            "base_indicator_id": str(sample_indicator.id)
        }

        # ACT
        response = await async_client.post(
            "/api/custom-factors",
            json=factor_data
        )

        # ASSERT
        assert response.status_code == 201
        data = response.json()
        assert data["base_indicator_id"] == str(sample_indicator.id)

    async def test_create_factor_missing_required_fields(
        self,
        async_client: AsyncClient
    ):
        """Test creating factor with missing required fields."""
        # ARRANGE
        factor_data = {
            "factor_name": "不完整因子"
            # Missing formula and formula_language
        }

        # ACT
        response = await async_client.post(
            "/api/custom-factors",
            json=factor_data
        )

        # ASSERT
        assert response.status_code == 422  # Validation error

    async def test_create_factor_invalid_formula_language(
        self,
        async_client: AsyncClient
    ):
        """Test creating factor with invalid formula language."""
        # ARRANGE
        factor_data = {
            "factor_name": "测试因子",
            "formula": "close > open",
            "formula_language": "invalid_language"
        }

        # ACT
        response = await async_client.post(
            "/api/custom-factors",
            json=factor_data
        )

        # ASSERT
        assert response.status_code == 400  # Business logic validation error


@pytest.mark.asyncio
class TestListUserFactors:
    """Test GET /api/custom-factors endpoint."""

    async def test_list_user_factors_success(
        self,
        async_client: AsyncClient,
        sample_custom_factor: CustomFactor
    ):
        """Test listing user's custom factors."""
        # ACT
        response = await async_client.get("/api/custom-factors")

        # ASSERT
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1
        assert len(data["factors"]) >= 1
        assert "skip" in data
        assert "limit" in data

        # Verify factor structure
        factor = data["factors"][0]
        assert "id" in factor
        assert "factor_name" in factor
        assert "formula" in factor
        assert "status" in factor
        assert "user_id" in factor

    async def test_list_user_factors_with_pagination(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession
    ):
        """Test listing user factors with custom pagination."""
        # ARRANGE
        # Create multiple factors
        for i in range(10):
            factor = CustomFactor(
                factor_name=f"因子{i}",
                user_id="user123",
                formula=f"close * {i}",
                formula_language="qlib_alpha",
                status=FactorStatus.DRAFT.value
            )
            db_session.add(factor)
        await db_session.commit()

        skip = 3
        limit = 5

        # ACT
        response = await async_client.get(
            f"/api/custom-factors?skip={skip}&limit={limit}"
        )

        # ASSERT
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 10
        assert len(data["factors"]) == 5
        assert data["skip"] == skip
        assert data["limit"] == limit

    async def test_list_user_factors_filter_by_status(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession
    ):
        """Test listing user factors filtered by status."""
        # ARRANGE
        # Create factors with different statuses
        draft_factor = CustomFactor(
            factor_name="草稿因子",
            user_id="user123",
            formula="close",
            formula_language="qlib_alpha",
            status=FactorStatus.DRAFT.value
        )
        published_factor = CustomFactor(
            factor_name="已发布因子",
            user_id="user123",
            formula="open",
            formula_language="qlib_alpha",
            status=FactorStatus.PUBLISHED.value
        )
        db_session.add_all([draft_factor, published_factor])
        await db_session.commit()

        # ACT
        response = await async_client.get(
            f"/api/custom-factors?status={FactorStatus.DRAFT.value}"
        )

        # ASSERT
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1
        for factor in data["factors"]:
            assert factor["status"] == FactorStatus.DRAFT.value

    async def test_list_user_factors_empty_list(
        self,
        async_client: AsyncClient
    ):
        """Test listing factors when user has none."""
        # ACT
        response = await async_client.get("/api/custom-factors")

        # ASSERT
        assert response.status_code == 200
        data = response.json()
        # May have 0 or more factors depending on fixtures
        assert "total" in data
        assert "factors" in data


@pytest.mark.asyncio
class TestGetFactorDetail:
    """Test GET /api/custom-factors/{factor_id} endpoint."""

    async def test_get_factor_detail_success(
        self,
        async_client: AsyncClient,
        sample_custom_factor: CustomFactor
    ):
        """Test getting factor detail by ID."""
        # ACT
        response = await async_client.get(
            f"/api/custom-factors/{sample_custom_factor.id}"
        )

        # ASSERT
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(sample_custom_factor.id)
        assert data["factor_name"] == sample_custom_factor.factor_name
        assert data["formula"] == sample_custom_factor.formula
        assert data["user_id"] == sample_custom_factor.user_id

    async def test_get_factor_detail_not_found(
        self,
        async_client: AsyncClient
    ):
        """Test getting factor detail with non-existent ID."""
        # ARRANGE
        non_existent_id = "00000000-0000-0000-0000-000000000000"

        # ACT
        response = await async_client.get(
            f"/api/custom-factors/{non_existent_id}"
        )

        # ASSERT
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data

    async def test_get_factor_detail_unauthorized_user(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession
    ):
        """Test getting factor detail for another user's factor."""
        # ARRANGE
        # Create factor belonging to different user
        other_user_factor = CustomFactor(
            factor_name="其他用户因子",
            user_id="user999",  # Different from mock user_id "user123"
            formula="close",
            formula_language="qlib_alpha",
            status=FactorStatus.DRAFT.value,
            is_public=False
        )
        db_session.add(other_user_factor)
        await db_session.commit()
        await db_session.refresh(other_user_factor)

        # ACT
        response = await async_client.get(
            f"/api/custom-factors/{other_user_factor.id}"
        )

        # ASSERT
        assert response.status_code == 404  # Access denied treated as not found


@pytest.mark.asyncio
class TestUpdateCustomFactor:
    """Test PUT /api/custom-factors/{factor_id} endpoint."""

    async def test_update_factor_success(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession,
        sample_custom_factor: CustomFactor
    ):
        """Test updating a custom factor."""
        # ARRANGE
        update_data = {
            "factor_name": "更新后的因子名",
            "description": "更新后的描述"
        }

        # ACT
        response = await async_client.put(
            f"/api/custom-factors/{sample_custom_factor.id}",
            json=update_data
        )

        # ASSERT
        assert response.status_code == 200
        data = response.json()
        assert data["factor_name"] == update_data["factor_name"]
        assert data["description"] == update_data["description"]

        # Verify database was updated
        await db_session.refresh(sample_custom_factor)
        assert sample_custom_factor.factor_name == update_data["factor_name"]

    async def test_update_factor_formula(
        self,
        async_client: AsyncClient,
        sample_custom_factor: CustomFactor
    ):
        """Test updating factor formula."""
        # ARRANGE
        update_data = {
            "formula": "(close - low) / (high - low)"
        }

        # ACT
        response = await async_client.put(
            f"/api/custom-factors/{sample_custom_factor.id}",
            json=update_data
        )

        # ASSERT
        assert response.status_code == 200
        data = response.json()
        assert data["formula"] == update_data["formula"]

    async def test_update_factor_not_found(
        self,
        async_client: AsyncClient
    ):
        """Test updating non-existent factor."""
        # ARRANGE
        non_existent_id = "00000000-0000-0000-0000-000000000000"
        update_data = {"factor_name": "新名称"}

        # ACT
        response = await async_client.put(
            f"/api/custom-factors/{non_existent_id}",
            json=update_data
        )

        # ASSERT
        assert response.status_code == 404

    async def test_update_factor_unauthorized(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession
    ):
        """Test updating another user's factor."""
        # ARRANGE
        other_user_factor = CustomFactor(
            factor_name="其他用户因子",
            user_id="user999",
            formula="close",
            formula_language="qlib_alpha",
            status=FactorStatus.DRAFT.value
        )
        db_session.add(other_user_factor)
        await db_session.commit()
        await db_session.refresh(other_user_factor)

        update_data = {"factor_name": "尝试更新"}

        # ACT
        response = await async_client.put(
            f"/api/custom-factors/{other_user_factor.id}",
            json=update_data
        )

        # ASSERT
        assert response.status_code == 404  # Access denied


@pytest.mark.asyncio
class TestDeleteCustomFactor:
    """Test DELETE /api/custom-factors/{factor_id} endpoint."""

    async def test_delete_factor_success(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession,
        sample_custom_factor: CustomFactor
    ):
        """Test deleting a custom factor."""
        # ARRANGE
        factor_id = sample_custom_factor.id

        # ACT
        response = await async_client.delete(
            f"/api/custom-factors/{factor_id}"
        )

        # ASSERT
        assert response.status_code == 204
        assert response.content == b""

        # Verify factor was soft deleted (is_deleted flag set to True)
        await db_session.refresh(sample_custom_factor)
        assert sample_custom_factor.is_deleted is True

    async def test_delete_factor_not_found(
        self,
        async_client: AsyncClient
    ):
        """Test deleting non-existent factor."""
        # ARRANGE
        non_existent_id = "00000000-0000-0000-0000-000000000000"

        # ACT
        response = await async_client.delete(
            f"/api/custom-factors/{non_existent_id}"
        )

        # ASSERT
        assert response.status_code == 404

    async def test_delete_factor_unauthorized(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession
    ):
        """Test deleting another user's factor."""
        # ARRANGE
        other_user_factor = CustomFactor(
            factor_name="其他用户因子",
            user_id="user999",
            formula="close",
            formula_language="qlib_alpha",
            status=FactorStatus.DRAFT.value
        )
        db_session.add(other_user_factor)
        await db_session.commit()
        await db_session.refresh(other_user_factor)

        # ACT
        response = await async_client.delete(
            f"/api/custom-factors/{other_user_factor.id}"
        )

        # ASSERT
        assert response.status_code == 404  # Access denied


@pytest.mark.asyncio
class TestPublishCustomFactor:
    """Test POST /api/custom-factors/{factor_id}/publish endpoint."""

    async def test_publish_factor_success(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession,
        sample_custom_factor: CustomFactor
    ):
        """Test publishing a custom factor."""
        # ARRANGE
        assert sample_custom_factor.status == FactorStatus.DRAFT.value
        publish_data = {"is_public": True}

        # ACT
        response = await async_client.post(
            f"/api/custom-factors/{sample_custom_factor.id}/publish",
            json=publish_data
        )

        # ASSERT
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == FactorStatus.PUBLISHED.value
        assert data["is_public"] is True

        # Verify database was updated
        await db_session.refresh(sample_custom_factor)
        assert sample_custom_factor.status == FactorStatus.PUBLISHED.value
        assert sample_custom_factor.is_public is True

    async def test_publish_factor_as_private(
        self,
        async_client: AsyncClient,
        sample_custom_factor: CustomFactor
    ):
        """Test publishing a factor as private."""
        # ARRANGE
        publish_data = {"is_public": False}

        # ACT
        response = await async_client.post(
            f"/api/custom-factors/{sample_custom_factor.id}/publish",
            json=publish_data
        )

        # ASSERT
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == FactorStatus.PUBLISHED.value
        assert data["is_public"] is False

    async def test_publish_factor_not_found(
        self,
        async_client: AsyncClient
    ):
        """Test publishing non-existent factor."""
        # ARRANGE
        non_existent_id = "00000000-0000-0000-0000-000000000000"
        publish_data = {"is_public": True}

        # ACT
        response = await async_client.post(
            f"/api/custom-factors/{non_existent_id}/publish",
            json=publish_data
        )

        # ASSERT
        assert response.status_code == 404


@pytest.mark.asyncio
class TestCloneCustomFactor:
    """Test POST /api/custom-factors/{factor_id}/clone endpoint."""

    async def test_clone_factor_success(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession,
        sample_public_factor: CustomFactor
    ):
        """Test cloning a public factor."""
        # ARRANGE
        clone_data = {"new_name": "克隆的动量因子"}

        # ACT
        response = await async_client.post(
            f"/api/custom-factors/{sample_public_factor.id}/clone",
            json=clone_data
        )

        # ASSERT
        assert response.status_code == 201
        data = response.json()
        assert data["factor_name"] == clone_data["new_name"]
        assert data["formula"] == sample_public_factor.formula
        assert data["user_id"] == "user123"  # Current mock user
        assert data["status"] == FactorStatus.DRAFT.value
        assert data["id"] != str(sample_public_factor.id)  # New factor ID

    async def test_clone_factor_updates_clone_count(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession,
        sample_public_factor: CustomFactor
    ):
        """Test cloning increments the clone count."""
        # ARRANGE
        original_clone_count = sample_public_factor.clone_count
        clone_data = {"new_name": "克隆因子"}

        # ACT
        response = await async_client.post(
            f"/api/custom-factors/{sample_public_factor.id}/clone",
            json=clone_data
        )

        # ASSERT
        assert response.status_code == 201

        # Verify clone count was incremented
        await db_session.refresh(sample_public_factor)
        assert sample_public_factor.clone_count == original_clone_count + 1

    async def test_clone_factor_not_found(
        self,
        async_client: AsyncClient
    ):
        """Test cloning non-existent factor."""
        # ARRANGE
        non_existent_id = "00000000-0000-0000-0000-000000000000"
        clone_data = {"new_name": "克隆因子"}

        # ACT
        response = await async_client.post(
            f"/api/custom-factors/{non_existent_id}/clone",
            json=clone_data
        )

        # ASSERT
        assert response.status_code == 404

    async def test_clone_factor_missing_new_name(
        self,
        async_client: AsyncClient,
        sample_public_factor: CustomFactor
    ):
        """Test cloning without providing new name."""
        # ACT
        response = await async_client.post(
            f"/api/custom-factors/{sample_public_factor.id}/clone",
            json={}
        )

        # ASSERT
        assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
class TestCustomFactorAPIErrorHandling:
    """Test error handling for Custom Factor API endpoints."""

    async def test_create_factor_with_invalid_json(
        self,
        async_client: AsyncClient
    ):
        """Test creating factor with invalid JSON payload."""
        # ACT
        response = await async_client.post(
            "/api/custom-factors",
            content="invalid json",
            headers={"Content-Type": "application/json"}
        )

        # ASSERT
        assert response.status_code == 422

    async def test_update_factor_with_empty_payload(
        self,
        async_client: AsyncClient,
        sample_custom_factor: CustomFactor
    ):
        """Test updating factor with empty payload."""
        # ACT
        response = await async_client.put(
            f"/api/custom-factors/{sample_custom_factor.id}",
            json={}
        )

        # ASSERT
        # Empty update should still succeed (no changes)
        assert response.status_code == 200


@pytest.mark.asyncio
class TestCustomFactorAPIResponseFormat:
    """Test response format consistency for Custom Factor API."""

    async def test_factor_response_includes_all_fields(
        self,
        async_client: AsyncClient,
        sample_custom_factor: CustomFactor
    ):
        """Test factor response includes all required fields."""
        # ACT
        response = await async_client.get(
            f"/api/custom-factors/{sample_custom_factor.id}"
        )

        # ASSERT
        assert response.status_code == 200
        data = response.json()

        # Verify all required fields
        required_fields = [
            "id", "factor_name", "formula", "formula_language",
            "status", "is_public", "user_id", "usage_count",
            "created_at", "updated_at"
        ]
        for field in required_fields:
            assert field in data

    async def test_list_response_pagination_metadata(
        self,
        async_client: AsyncClient
    ):
        """Test list response includes pagination metadata."""
        # ACT
        response = await async_client.get("/api/custom-factors")

        # ASSERT
        assert response.status_code == 200
        data = response.json()

        # Verify pagination fields
        assert "total" in data
        assert "skip" in data
        assert "limit" in data
        assert "factors" in data


@pytest.mark.asyncio
class TestCustomFactorAPIServiceErrorHandling:
    """Test service-level error handling for Custom Factor API."""

    async def test_create_factor_service_value_error(
        self,
        async_client: AsyncClient,
        monkeypatch
    ):
        """Test creating factor handles service ValueError."""
        # ARRANGE
        from app.modules.indicator.services import custom_factor_service

        async def mock_create_factor(*args, **kwargs):
            raise ValueError("Invalid formula syntax")

        monkeypatch.setattr(
            custom_factor_service.CustomFactorService,
            "create_factor",
            mock_create_factor
        )

        factor_data = {
            "factor_name": "测试因子",
            "formula": "invalid formula",
            "formula_language": "qlib_alpha"
        }

        # ACT
        response = await async_client.post(
            "/api/custom-factors",
            json=factor_data
        )

        # ASSERT
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "Invalid formula syntax" in data["detail"]

    async def test_create_factor_service_unexpected_error(
        self,
        async_client: AsyncClient,
        monkeypatch
    ):
        """Test creating factor handles unexpected service errors."""
        # ARRANGE
        from app.modules.indicator.services import custom_factor_service

        async def mock_create_factor(*args, **kwargs):
            raise Exception("Unexpected database error")

        monkeypatch.setattr(
            custom_factor_service.CustomFactorService,
            "create_factor",
            mock_create_factor
        )

        factor_data = {
            "factor_name": "测试因子",
            "formula": "close",
            "formula_language": "qlib_alpha"
        }

        # ACT
        response = await async_client.post(
            "/api/custom-factors",
            json=factor_data
        )

        # ASSERT
        assert response.status_code == 500
        data = response.json()
        assert "detail" in data
        assert "Failed to create factor" in data["detail"]

    async def test_list_user_factors_service_error(
        self,
        async_client: AsyncClient,
        monkeypatch
    ):
        """Test listing factors handles service errors."""
        # ARRANGE
        from app.modules.indicator.services import custom_factor_service

        async def mock_get_user_factors(*args, **kwargs):
            raise Exception("Database connection lost")

        monkeypatch.setattr(
            custom_factor_service.CustomFactorService,
            "get_user_factors",
            mock_get_user_factors
        )

        # ACT
        response = await async_client.get("/api/custom-factors")

        # ASSERT
        assert response.status_code == 500
        data = response.json()
        assert "detail" in data
        assert "Failed to list factors" in data["detail"]

    async def test_get_factor_detail_service_error(
        self,
        async_client: AsyncClient,
        monkeypatch
    ):
        """Test getting factor detail handles service errors."""
        # ARRANGE
        from app.modules.indicator.services import custom_factor_service

        async def mock_get_factor_detail(*args, **kwargs):
            raise Exception("Database timeout")

        monkeypatch.setattr(
            custom_factor_service.CustomFactorService,
            "get_factor_detail",
            mock_get_factor_detail
        )

        # ACT
        response = await async_client.get(
            "/api/custom-factors/test-id"
        )

        # ASSERT
        assert response.status_code == 500
        data = response.json()
        assert "detail" in data
        assert "Failed to get factor" in data["detail"]

    async def test_update_factor_service_value_error(
        self,
        async_client: AsyncClient,
        monkeypatch
    ):
        """Test updating factor handles service ValueError."""
        # ARRANGE
        from app.modules.indicator.services import custom_factor_service

        async def mock_update_factor(*args, **kwargs):
            raise ValueError("Cannot update published factor")

        monkeypatch.setattr(
            custom_factor_service.CustomFactorService,
            "update_factor",
            mock_update_factor
        )

        update_data = {"factor_name": "新名称"}

        # ACT
        response = await async_client.put(
            "/api/custom-factors/test-id",
            json=update_data
        )

        # ASSERT
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "Cannot update published factor" in data["detail"]

    async def test_update_factor_service_unexpected_error(
        self,
        async_client: AsyncClient,
        monkeypatch
    ):
        """Test updating factor handles unexpected service errors."""
        # ARRANGE
        from app.modules.indicator.services import custom_factor_service

        async def mock_update_factor(*args, **kwargs):
            raise Exception("Unexpected error")

        monkeypatch.setattr(
            custom_factor_service.CustomFactorService,
            "update_factor",
            mock_update_factor
        )

        update_data = {"factor_name": "新名称"}

        # ACT
        response = await async_client.put(
            "/api/custom-factors/test-id",
            json=update_data
        )

        # ASSERT
        assert response.status_code == 500
        data = response.json()
        assert "detail" in data
        assert "Failed to update factor" in data["detail"]

    async def test_delete_factor_service_error(
        self,
        async_client: AsyncClient,
        monkeypatch
    ):
        """Test deleting factor handles service errors."""
        # ARRANGE
        from app.modules.indicator.services import custom_factor_service

        async def mock_delete_factor(*args, **kwargs):
            raise Exception("Database error")

        monkeypatch.setattr(
            custom_factor_service.CustomFactorService,
            "delete_factor",
            mock_delete_factor
        )

        # ACT
        response = await async_client.delete(
            "/api/custom-factors/test-id"
        )

        # ASSERT
        assert response.status_code == 500
        data = response.json()
        assert "detail" in data
        assert "Failed to delete factor" in data["detail"]

    async def test_publish_factor_service_error(
        self,
        async_client: AsyncClient,
        monkeypatch
    ):
        """Test publishing factor handles service errors."""
        # ARRANGE
        from app.modules.indicator.services import custom_factor_service

        async def mock_publish_factor(*args, **kwargs):
            raise Exception("Publication failed")

        monkeypatch.setattr(
            custom_factor_service.CustomFactorService,
            "publish_factor",
            mock_publish_factor
        )

        publish_data = {"is_public": True}

        # ACT
        response = await async_client.post(
            "/api/custom-factors/test-id/publish",
            json=publish_data
        )

        # ASSERT
        assert response.status_code == 500
        data = response.json()
        assert "detail" in data
        assert "Failed to publish factor" in data["detail"]

    async def test_clone_factor_service_error(
        self,
        async_client: AsyncClient,
        monkeypatch
    ):
        """Test cloning factor handles service errors."""
        # ARRANGE
        from app.modules.indicator.services import custom_factor_service

        async def mock_clone_factor(*args, **kwargs):
            raise Exception("Clone operation failed")

        monkeypatch.setattr(
            custom_factor_service.CustomFactorService,
            "clone_factor",
            mock_clone_factor
        )

        clone_data = {"new_name": "克隆因子"}

        # ACT
        response = await async_client.post(
            "/api/custom-factors/test-id/clone",
            json=clone_data
        )

        # ASSERT
        assert response.status_code == 500
        data = response.json()
        assert "detail" in data
        assert "Failed to clone factor" in data["detail"]


@pytest.mark.asyncio
class TestCustomFactorAPICorrelationID:
    """Test correlation ID handling for Custom Factor API."""

    async def test_create_factor_with_custom_correlation_id(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession
    ):
        """Test creating factor with custom correlation ID header."""
        # ARRANGE
        correlation_id = "custom-correlation-12345"
        headers = {"X-Correlation-ID": correlation_id}
        factor_data = {
            "factor_name": "测试因子",
            "formula": "close",
            "formula_language": "qlib_alpha"
        }

        # ACT
        response = await async_client.post(
            "/api/custom-factors",
            json=factor_data,
            headers=headers
        )

        # ASSERT
        assert response.status_code == 201

    async def test_create_factor_generates_correlation_id(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession
    ):
        """Test creating factor generates correlation ID when not provided."""
        # ARRANGE
        factor_data = {
            "factor_name": "测试因子",
            "formula": "close",
            "formula_language": "qlib_alpha"
        }

        # ACT
        response = await async_client.post(
            "/api/custom-factors",
            json=factor_data
        )

        # ASSERT
        assert response.status_code == 201

    async def test_list_factors_with_correlation_id(
        self,
        async_client: AsyncClient
    ):
        """Test listing factors with correlation ID header."""
        # ARRANGE
        correlation_id = "list-correlation-123"
        headers = {"X-Correlation-ID": correlation_id}

        # ACT
        response = await async_client.get(
            "/api/custom-factors",
            headers=headers
        )

        # ASSERT
        assert response.status_code == 200


@pytest.mark.asyncio
class TestCustomFactorAPIPaginationEdgeCases:
    """Test pagination edge cases for Custom Factor API."""

    async def test_list_factors_with_zero_limit(
        self,
        async_client: AsyncClient
    ):
        """Test listing factors with limit=0 (invalid)."""
        # ACT
        response = await async_client.get("/api/custom-factors?limit=0")

        # ASSERT
        assert response.status_code == 422  # Validation error

    async def test_list_factors_with_maximum_limit(
        self,
        async_client: AsyncClient
    ):
        """Test listing factors with maximum allowed limit."""
        # ACT
        response = await async_client.get("/api/custom-factors?limit=1000")

        # ASSERT
        assert response.status_code == 200
        data = response.json()
        assert data["limit"] == 1000

    async def test_list_factors_exceeding_maximum_limit(
        self,
        async_client: AsyncClient
    ):
        """Test listing factors with limit exceeding maximum."""
        # ACT
        response = await async_client.get("/api/custom-factors?limit=1001")

        # ASSERT
        assert response.status_code == 422  # Validation error

    async def test_list_factors_with_negative_skip(
        self,
        async_client: AsyncClient
    ):
        """Test listing factors with negative skip value."""
        # ACT
        response = await async_client.get("/api/custom-factors?skip=-1")

        # ASSERT
        assert response.status_code == 422  # Validation error
