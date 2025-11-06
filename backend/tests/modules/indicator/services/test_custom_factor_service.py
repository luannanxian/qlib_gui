"""
TDD Tests for CustomFactorService

Comprehensive test suite covering:
- Factor CRUD operations with authorization
- Publishing workflow (draft → published → public)
- Factor cloning
- Search functionality
- Data validation
- Exception handling
- Authorization checks
- Edge cases

Following TDD best practices:
- AAA pattern (Arrange-Act-Assert)
- Single responsibility per test
- Clear test naming
- Fixture-based test data
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from app.database.models.indicator import CustomFactor, IndicatorComponent, FactorStatus
from app.modules.indicator.services.custom_factor_service import CustomFactorService
from app.modules.indicator.exceptions import ValidationError, ConflictError


@pytest.mark.asyncio
class TestCustomFactorServiceCreate:
    """Test create_factor functionality."""

    async def test_create_factor_with_valid_data(
        self,
        custom_factor_service: CustomFactorService,
        sample_indicator: IndicatorComponent,
        db_session: AsyncSession
    ):
        """Test creating a factor with valid data."""
        # ARRANGE
        factor_data = {
            "factor_name": "测试因子",
            "formula": "(close - open) / open",
            "formula_language": "qlib_alpha",
            "description": "测试因子描述",
            "base_indicator_id": sample_indicator.id
        }
        user_id = "user123"

        # ACT
        result = await custom_factor_service.create_factor(factor_data, user_id)

        # ASSERT
        assert "factor" in result
        assert "message" in result
        assert result["factor"]["factor_name"] == "测试因子"
        assert result["factor"]["user_id"] == user_id
        assert result["factor"]["formula"] == "(close - open) / open"
        assert result["factor"]["status"] == FactorStatus.DRAFT.value
        assert result["factor"]["is_public"] is False

    async def test_create_factor_with_minimal_data(
        self,
        custom_factor_service: CustomFactorService,
        db_session: AsyncSession
    ):
        """Test creating a factor with minimal required data."""
        # ARRANGE
        factor_data = {
            "factor_name": "最小因子",
            "formula": "close",
            "formula_language": "qlib_alpha"
        }
        user_id = "user456"

        # ACT
        result = await custom_factor_service.create_factor(factor_data, user_id)

        # ASSERT
        assert result["factor"]["factor_name"] == "最小因子"
        assert result["factor"]["user_id"] == user_id
        assert result["factor"]["status"] == FactorStatus.DRAFT.value

    async def test_create_factor_missing_required_fields(
        self,
        custom_factor_service: CustomFactorService
    ):
        """Test creating a factor with missing required fields."""
        # ARRANGE
        factor_data = {
            "factor_name": "测试因子"
            # Missing: formula, formula_language
        }
        user_id = "user123"

        # ACT & ASSERT
        with pytest.raises(ValidationError) as exc_info:
            await custom_factor_service.create_factor(factor_data, user_id)

        assert "Missing required fields" in str(exc_info.value)
        assert "formula" in str(exc_info.value)

    async def test_create_factor_invalid_formula_language(
        self,
        custom_factor_service: CustomFactorService
    ):
        """Test creating a factor with invalid formula_language."""
        # ARRANGE
        factor_data = {
            "factor_name": "测试因子",
            "formula": "close",
            "formula_language": "invalid_language"
        }
        user_id = "user123"

        # ACT & ASSERT
        with pytest.raises(ValidationError) as exc_info:
            await custom_factor_service.create_factor(factor_data, user_id)

        assert "Invalid formula_language" in str(exc_info.value)

    async def test_create_factor_user_id_override_prevention(
        self,
        custom_factor_service: CustomFactorService,
        db_session: AsyncSession
    ):
        """Test that user_id in data is overridden by authenticated user."""
        # ARRANGE
        factor_data = {
            "factor_name": "授权测试",
            "formula": "close",
            "formula_language": "qlib_alpha",
            "user_id": "malicious_user"  # Should be overridden
        }
        authenticated_user_id = "real_user"

        # ACT
        result = await custom_factor_service.create_factor(factor_data, authenticated_user_id)

        # ASSERT
        # user_id should be from authenticated_user_id, not from data
        assert result["factor"]["user_id"] == authenticated_user_id
        assert result["factor"]["user_id"] != "malicious_user"

    async def test_create_factor_with_all_languages(
        self,
        custom_factor_service: CustomFactorService,
        db_session: AsyncSession
    ):
        """Test creating factors with all valid formula languages."""
        # ARRANGE
        languages = ["qlib_alpha", "python", "pandas"]
        user_id = "user123"

        # ACT & ASSERT
        for lang in languages:
            factor_data = {
                "factor_name": f"因子_{lang}",
                "formula": "close",
                "formula_language": lang
            }
            result = await custom_factor_service.create_factor(factor_data, user_id)
            assert result["factor"]["formula_language"] == lang


@pytest.mark.asyncio
class TestCustomFactorServiceGetUserFactors:
    """Test get_user_factors functionality."""

    async def test_get_user_factors_default_pagination(
        self,
        custom_factor_service: CustomFactorService,
        db_session: AsyncSession
    ):
        """Test getting user's factors with default pagination."""
        # ARRANGE
        user_id = "user123"
        # Create multiple factors
        factors = [
            CustomFactor(
                factor_name=f"因子{i}",
                user_id=user_id,
                formula=f"close * {i}",
                formula_language="qlib_alpha",
                status=FactorStatus.DRAFT.value
            )
            for i in range(1, 6)
        ]
        for factor in factors:
            db_session.add(factor)
        await db_session.commit()

        # ACT
        result = await custom_factor_service.get_user_factors(user_id)

        # ASSERT
        assert result["total"] == 5
        assert len(result["factors"]) == 5

    async def test_get_user_factors_with_status_filter(
        self,
        custom_factor_service: CustomFactorService,
        db_session: AsyncSession
    ):
        """Test filtering user factors by status."""
        # ARRANGE
        user_id = "user123"
        draft = CustomFactor(
            factor_name="草稿因子",
            user_id=user_id,
            formula="close",
            formula_language="qlib_alpha",
            status=FactorStatus.DRAFT.value
        )
        published = CustomFactor(
            factor_name="已发布因子",
            user_id=user_id,
            formula="open",
            formula_language="qlib_alpha",
            status=FactorStatus.PUBLISHED.value
        )
        db_session.add(draft)
        db_session.add(published)
        await db_session.commit()

        # ACT
        result = await custom_factor_service.get_user_factors(
            user_id,
            status=FactorStatus.DRAFT.value
        )

        # ASSERT
        assert result["total"] == 1
        assert result["factors"][0]["factor_name"] == "草稿因子"

    async def test_get_user_factors_with_pagination(
        self,
        custom_factor_service: CustomFactorService,
        db_session: AsyncSession
    ):
        """Test pagination for user factors."""
        # ARRANGE
        user_id = "user123"
        factors = [
            CustomFactor(
                factor_name=f"因子{i}",
                user_id=user_id,
                formula=f"close * {i}",
                formula_language="qlib_alpha"
            )
            for i in range(1, 21)  # 20 factors
        ]
        for factor in factors:
            db_session.add(factor)
        await db_session.commit()

        # ACT
        result = await custom_factor_service.get_user_factors(
            user_id,
            skip=5,
            limit=10
        )

        # ASSERT
        assert result["total"] == 20
        assert len(result["factors"]) == 10
        assert result["skip"] == 5
        assert result["limit"] == 10

    async def test_get_user_factors_empty_result(
        self,
        custom_factor_service: CustomFactorService
    ):
        """Test getting factors for user with no factors."""
        # ARRANGE
        user_id = "user_with_no_factors"

        # ACT
        result = await custom_factor_service.get_user_factors(user_id)

        # ASSERT
        assert result["total"] == 0
        assert len(result["factors"]) == 0

    async def test_get_user_factors_only_own_factors(
        self,
        custom_factor_service: CustomFactorService,
        db_session: AsyncSession
    ):
        """Test that users only see their own factors."""
        # ARRANGE
        user1 = "user1"
        user2 = "user2"
        factor1 = CustomFactor(
            factor_name="用户1的因子",
            user_id=user1,
            formula="close",
            formula_language="qlib_alpha"
        )
        factor2 = CustomFactor(
            factor_name="用户2的因子",
            user_id=user2,
            formula="open",
            formula_language="qlib_alpha"
        )
        db_session.add(factor1)
        db_session.add(factor2)
        await db_session.commit()

        # ACT
        result = await custom_factor_service.get_user_factors(user1)

        # ASSERT
        assert result["total"] == 1
        assert result["factors"][0]["factor_name"] == "用户1的因子"


@pytest.mark.asyncio
class TestCustomFactorServiceGetDetail:
    """Test get_factor_detail functionality."""

    async def test_get_factor_detail_existing(
        self,
        custom_factor_service: CustomFactorService,
        sample_custom_factor: CustomFactor
    ):
        """Test getting detail for existing factor."""
        # ARRANGE
        factor_id = sample_custom_factor.id

        # ACT
        result = await custom_factor_service.get_factor_detail(factor_id)

        # ASSERT
        assert result is not None
        assert result["id"] == factor_id
        assert result["factor_name"] == "我的动量因子"
        assert "formula" in result
        assert "status" in result
        assert "user_id" in result

    async def test_get_factor_detail_nonexistent(
        self,
        custom_factor_service: CustomFactorService
    ):
        """Test getting detail for non-existent factor."""
        # ARRANGE
        nonexistent_id = "00000000-0000-0000-0000-000000000000"

        # ACT
        result = await custom_factor_service.get_factor_detail(nonexistent_id)

        # ASSERT
        assert result is None


@pytest.mark.asyncio
class TestCustomFactorServicePublish:
    """Test publish_factor functionality."""

    async def test_publish_factor_by_owner(
        self,
        custom_factor_service: CustomFactorService,
        sample_custom_factor: CustomFactor,
        db_session: AsyncSession
    ):
        """Test publishing a factor by its owner."""
        # ARRANGE
        factor_id = sample_custom_factor.id
        user_id = sample_custom_factor.user_id
        assert sample_custom_factor.status == FactorStatus.DRAFT.value

        # ACT
        result = await custom_factor_service.publish_factor(factor_id, user_id)

        # ASSERT
        assert result is not None
        assert result["factor"]["status"] == FactorStatus.PUBLISHED.value
        assert "message" in result

        # Verify in database
        await db_session.refresh(sample_custom_factor)
        assert sample_custom_factor.status == FactorStatus.PUBLISHED.value
        assert sample_custom_factor.published_at is not None

    async def test_publish_factor_by_non_owner(
        self,
        custom_factor_service: CustomFactorService,
        sample_custom_factor: CustomFactor
    ):
        """Test publishing a factor by non-owner (should fail)."""
        # ARRANGE
        factor_id = sample_custom_factor.id
        wrong_user_id = "different_user"

        # ACT
        result = await custom_factor_service.publish_factor(factor_id, wrong_user_id)

        # ASSERT
        assert result is None

    async def test_publish_nonexistent_factor(
        self,
        custom_factor_service: CustomFactorService
    ):
        """Test publishing non-existent factor."""
        # ARRANGE
        nonexistent_id = "00000000-0000-0000-0000-000000000000"
        user_id = "user123"

        # ACT
        result = await custom_factor_service.publish_factor(nonexistent_id, user_id)

        # ASSERT
        assert result is None


@pytest.mark.asyncio
class TestCustomFactorServiceMakePublic:
    """Test make_public functionality."""

    async def test_make_public_by_owner(
        self,
        custom_factor_service: CustomFactorService,
        db_session: AsyncSession
    ):
        """Test making a factor public by its owner."""
        # ARRANGE
        user_id = "user123"
        factor = CustomFactor(
            factor_name="待公开因子",
            user_id=user_id,
            formula="close",
            formula_language="qlib_alpha",
            status=FactorStatus.PUBLISHED.value,
            is_public=False
        )
        db_session.add(factor)
        await db_session.commit()
        await db_session.refresh(factor)

        # ACT
        result = await custom_factor_service.make_public(factor.id, user_id)

        # ASSERT
        assert result is not None
        assert result["factor"]["is_public"] is True
        assert "message" in result

        # Verify in database
        await db_session.refresh(factor)
        assert factor.is_public is True
        assert factor.shared_at is not None

    async def test_make_public_by_non_owner(
        self,
        custom_factor_service: CustomFactorService,
        sample_custom_factor: CustomFactor
    ):
        """Test making a factor public by non-owner (should fail)."""
        # ARRANGE
        factor_id = sample_custom_factor.id
        wrong_user_id = "different_user"

        # ACT
        result = await custom_factor_service.make_public(factor_id, wrong_user_id)

        # ASSERT
        assert result is None

    async def test_make_public_nonexistent_factor(
        self,
        custom_factor_service: CustomFactorService
    ):
        """Test making non-existent factor public."""
        # ARRANGE
        nonexistent_id = "00000000-0000-0000-0000-000000000000"
        user_id = "user123"

        # ACT
        result = await custom_factor_service.make_public(nonexistent_id, user_id)

        # ASSERT
        assert result is None


@pytest.mark.asyncio
class TestCustomFactorServiceClone:
    """Test clone_factor functionality."""

    async def test_clone_public_factor(
        self,
        custom_factor_service: CustomFactorService,
        sample_public_factor: CustomFactor,
        db_session: AsyncSession
    ):
        """Test cloning a public factor."""
        # ARRANGE
        source_id = sample_public_factor.id
        new_user_id = "clone_user"

        # ACT
        result = await custom_factor_service.clone_factor(source_id, new_user_id)

        # ASSERT
        assert result is not None
        assert result["factor"]["user_id"] == new_user_id
        assert result["factor"]["cloned_from_id"] == source_id
        assert result["factor"]["status"] == FactorStatus.DRAFT.value
        assert result["factor"]["is_public"] is False

    async def test_clone_factor_with_custom_name(
        self,
        custom_factor_service: CustomFactorService,
        sample_public_factor: CustomFactor
    ):
        """Test cloning a factor with custom name."""
        # ARRANGE
        source_id = sample_public_factor.id
        new_user_id = "clone_user"
        new_name = "我的克隆因子"

        # ACT
        result = await custom_factor_service.clone_factor(
            source_id,
            new_user_id,
            new_factor_name=new_name
        )

        # ASSERT
        assert result is not None
        assert result["factor"]["factor_name"] == new_name

    async def test_clone_non_public_factor(
        self,
        custom_factor_service: CustomFactorService,
        sample_custom_factor: CustomFactor
    ):
        """Test cloning a non-public factor (should fail)."""
        # ARRANGE
        source_id = sample_custom_factor.id
        new_user_id = "clone_user"
        assert sample_custom_factor.is_public is False

        # ACT
        result = await custom_factor_service.clone_factor(source_id, new_user_id)

        # ASSERT
        assert result is None

    async def test_clone_nonexistent_factor(
        self,
        custom_factor_service: CustomFactorService
    ):
        """Test cloning non-existent factor."""
        # ARRANGE
        nonexistent_id = "00000000-0000-0000-0000-000000000000"
        new_user_id = "clone_user"

        # ACT
        result = await custom_factor_service.clone_factor(nonexistent_id, new_user_id)

        # ASSERT
        assert result is None

    async def test_clone_increments_clone_count(
        self,
        custom_factor_service: CustomFactorService,
        sample_public_factor: CustomFactor,
        db_session: AsyncSession
    ):
        """Test that cloning increments the clone_count."""
        # ARRANGE
        source_id = sample_public_factor.id
        initial_clone_count = sample_public_factor.clone_count

        # ACT
        await custom_factor_service.clone_factor(source_id, "user1")
        await custom_factor_service.clone_factor(source_id, "user2")

        # ASSERT
        await db_session.refresh(sample_public_factor)
        assert sample_public_factor.clone_count == initial_clone_count + 2


@pytest.mark.asyncio
class TestCustomFactorServiceSearch:
    """Test search_public_factors functionality."""

    async def test_search_public_factors_by_name(
        self,
        custom_factor_service: CustomFactorService,
        sample_public_factor: CustomFactor
    ):
        """Test searching public factors by name."""
        # ARRANGE
        keyword = "动量"

        # ACT
        result = await custom_factor_service.search_public_factors(keyword)

        # ASSERT
        assert result["total"] >= 0
        assert result["keyword"] == keyword
        # Only public factors should be returned
        for factor in result["factors"]:
            assert factor["is_public"] is True
            assert factor["status"] == FactorStatus.PUBLISHED.value

    async def test_search_public_factors_excludes_private(
        self,
        custom_factor_service: CustomFactorService,
        sample_custom_factor: CustomFactor,
        sample_public_factor: CustomFactor
    ):
        """Test that search excludes private factors."""
        # ARRANGE
        keyword = "因子"

        # ACT
        result = await custom_factor_service.search_public_factors(keyword)

        # ASSERT
        # All results should be public
        for factor in result["factors"]:
            assert factor["is_public"] is True

    async def test_search_public_factors_with_pagination(
        self,
        custom_factor_service: CustomFactorService,
        db_session: AsyncSession
    ):
        """Test search with pagination."""
        # ARRANGE
        # Create multiple public factors
        factors = [
            CustomFactor(
                factor_name=f"公开因子{i}",
                user_id=f"user{i}",
                formula=f"close * {i}",
                formula_language="qlib_alpha",
                status=FactorStatus.PUBLISHED.value,
                is_public=True
            )
            for i in range(1, 11)
        ]
        for factor in factors:
            db_session.add(factor)
        await db_session.commit()

        # ACT
        result = await custom_factor_service.search_public_factors(
            keyword="因子",
            skip=3,
            limit=5
        )

        # ASSERT
        assert len(result["factors"]) <= 5

    async def test_search_public_factors_no_results(
        self,
        custom_factor_service: CustomFactorService
    ):
        """Test search with no matching results."""
        # ARRANGE
        keyword = "XYZ_NONEXISTENT_999"

        # ACT
        result = await custom_factor_service.search_public_factors(keyword)

        # ASSERT
        assert len(result["factors"]) == 0


@pytest.mark.asyncio
class TestCustomFactorServicePopular:
    """Test get_popular_factors functionality."""

    async def test_get_popular_factors_default_limit(
        self,
        custom_factor_service: CustomFactorService,
        db_session: AsyncSession
    ):
        """Test getting popular factors with default limit."""
        # ARRANGE
        factors = [
            CustomFactor(
                factor_name=f"流行因子{i}",
                user_id="user123",
                formula=f"close * {i}",
                formula_language="qlib_alpha",
                status=FactorStatus.PUBLISHED.value,
                is_public=True,
                usage_count=i * 100
            )
            for i in range(1, 16)
        ]
        for factor in factors:
            db_session.add(factor)
        await db_session.commit()

        # ACT
        result = await custom_factor_service.get_popular_factors(limit=10)

        # ASSERT
        assert len(result["factors"]) <= 10
        assert result["total"] == len(result["factors"])

        # Verify sorted by usage_count descending
        usage_counts = [f["usage_count"] for f in result["factors"]]
        assert usage_counts == sorted(usage_counts, reverse=True)

    async def test_get_popular_factors_empty_database(
        self,
        custom_factor_service: CustomFactorService
    ):
        """Test getting popular factors when no public factors exist."""
        # ARRANGE
        # No public factors

        # ACT
        result = await custom_factor_service.get_popular_factors()

        # ASSERT
        assert result["total"] == 0
        assert len(result["factors"]) == 0


@pytest.mark.asyncio
class TestCustomFactorServiceDelete:
    """Test delete_factor functionality."""

    async def test_delete_factor_by_owner(
        self,
        custom_factor_service: CustomFactorService,
        sample_custom_factor: CustomFactor,
        db_session: AsyncSession
    ):
        """Test deleting a factor by its owner."""
        # ARRANGE
        factor_id = sample_custom_factor.id
        user_id = sample_custom_factor.user_id

        # ACT
        success = await custom_factor_service.delete_factor(factor_id, user_id)

        # ASSERT
        assert success is True

        # Verify soft delete
        await db_session.refresh(sample_custom_factor)
        assert sample_custom_factor.is_deleted is True

    async def test_delete_factor_by_non_owner(
        self,
        custom_factor_service: CustomFactorService,
        sample_custom_factor: CustomFactor
    ):
        """Test deleting a factor by non-owner (should fail)."""
        # ARRANGE
        factor_id = sample_custom_factor.id
        wrong_user_id = "different_user"

        # ACT
        success = await custom_factor_service.delete_factor(factor_id, wrong_user_id)

        # ASSERT
        assert success is False

    async def test_delete_nonexistent_factor(
        self,
        custom_factor_service: CustomFactorService
    ):
        """Test deleting non-existent factor."""
        # ARRANGE
        nonexistent_id = "00000000-0000-0000-0000-000000000000"
        user_id = "user123"

        # ACT
        success = await custom_factor_service.delete_factor(nonexistent_id, user_id)

        # ASSERT
        assert success is False

    async def test_delete_factor_hard_delete(
        self,
        custom_factor_service: CustomFactorService,
        db_session: AsyncSession
    ):
        """Test hard delete of a factor."""
        # ARRANGE
        user_id = "user123"
        factor = CustomFactor(
            factor_name="待删除因子",
            user_id=user_id,
            formula="close",
            formula_language="qlib_alpha"
        )
        db_session.add(factor)
        await db_session.commit()
        await db_session.refresh(factor)
        factor_id = factor.id

        # ACT
        success = await custom_factor_service.delete_factor(
            factor_id,
            user_id,
            soft=False
        )

        # ASSERT
        assert success is True

        # Verify hard delete (should not be in database)
        from sqlalchemy import select
        result = await db_session.execute(
            select(CustomFactor).where(CustomFactor.id == factor_id)
        )
        deleted_factor = result.scalar_one_or_none()
        assert deleted_factor is None


@pytest.mark.asyncio
class TestCustomFactorServiceValidation:
    """Test data validation in CustomFactorService."""

    async def test_create_factor_empty_formula(
        self,
        custom_factor_service: CustomFactorService
    ):
        """Test creating factor with empty formula."""
        # ARRANGE
        factor_data = {
            "factor_name": "测试",
            "formula": "",  # Empty
            "formula_language": "qlib_alpha"
        }
        user_id = "user123"

        # ACT & ASSERT
        with pytest.raises(ValidationError):
            await custom_factor_service.create_factor(factor_data, user_id)

    async def test_create_factor_empty_name(
        self,
        custom_factor_service: CustomFactorService
    ):
        """Test creating factor with empty name."""
        # ARRANGE
        factor_data = {
            "factor_name": "",  # Empty
            "formula": "close",
            "formula_language": "qlib_alpha"
        }
        user_id = "user123"

        # ACT & ASSERT
        with pytest.raises(ValidationError):
            await custom_factor_service.create_factor(factor_data, user_id)

    async def test_create_factor_with_special_characters(
        self,
        custom_factor_service: CustomFactorService,
        db_session: AsyncSession
    ):
        """Test creating factor with special characters in name."""
        # ARRANGE
        factor_data = {
            "factor_name": "特殊字符@#$%因子",
            "formula": "close",
            "formula_language": "qlib_alpha"
        }
        user_id = "user123"

        # ACT
        result = await custom_factor_service.create_factor(factor_data, user_id)

        # ASSERT
        assert result["factor"]["factor_name"] == "特殊字符@#$%因子"


@pytest.mark.asyncio
class TestCustomFactorServiceEdgeCases:
    """Test edge cases and boundary conditions."""

    async def test_publishing_workflow_complete(
        self,
        custom_factor_service: CustomFactorService,
        db_session: AsyncSession
    ):
        """Test complete publishing workflow: draft → published → public."""
        # ARRANGE
        user_id = "user123"
        factor_data = {
            "factor_name": "工作流测试",
            "formula": "close",
            "formula_language": "qlib_alpha"
        }

        # ACT & ASSERT
        # Step 1: Create (draft)
        create_result = await custom_factor_service.create_factor(factor_data, user_id)
        factor_id = create_result["factor"]["id"]
        assert create_result["factor"]["status"] == FactorStatus.DRAFT.value
        assert create_result["factor"]["is_public"] is False

        # Step 2: Publish
        publish_result = await custom_factor_service.publish_factor(factor_id, user_id)
        assert publish_result["factor"]["status"] == FactorStatus.PUBLISHED.value
        assert publish_result["factor"]["is_public"] is False

        # Step 3: Make public
        public_result = await custom_factor_service.make_public(factor_id, user_id)
        assert public_result["factor"]["is_public"] is True

    @pytest.mark.skip(reason="Concurrent operations may fail in SQLite")
    async def test_concurrent_clone_operations(
        self,
        custom_factor_service: CustomFactorService,
        sample_public_factor: CustomFactor,
        db_session: AsyncSession
    ):
        """Test concurrent clone operations."""
        # ARRANGE
        source_id = sample_public_factor.id
        initial_clone_count = sample_public_factor.clone_count

        # ACT
        import asyncio
        tasks = [
            custom_factor_service.clone_factor(source_id, f"user{i}")
            for i in range(5)
        ]
        results = await asyncio.gather(*tasks)

        # ASSERT
        assert all(r is not None for r in results)
        await db_session.refresh(sample_public_factor)
        assert sample_public_factor.clone_count == initial_clone_count + 5

    async def test_large_formula_content(
        self,
        custom_factor_service: CustomFactorService,
        db_session: AsyncSession
    ):
        """Test creating factor with large formula."""
        # ARRANGE
        large_formula = "close " + "+ open " * 1000  # Large formula
        factor_data = {
            "factor_name": "大公式因子",
            "formula": large_formula,
            "formula_language": "qlib_alpha"
        }
        user_id = "user123"

        # ACT
        result = await custom_factor_service.create_factor(factor_data, user_id)

        # ASSERT
        assert result["factor"]["formula"] == large_formula

    async def test_unicode_content(
        self,
        custom_factor_service: CustomFactorService,
        db_session: AsyncSession
    ):
        """Test creating factor with Unicode content."""
        # ARRANGE
        factor_data = {
            "factor_name": "🚀Unicode因子😊",
            "formula": "close",
            "formula_language": "qlib_alpha",
            "description": "包含emoji和特殊字符：αβγδε"
        }
        user_id = "user123"

        # ACT
        result = await custom_factor_service.create_factor(factor_data, user_id)

        # ASSERT
        assert "🚀" in result["factor"]["factor_name"]
        assert "αβγδε" in result["factor"]["description"]
