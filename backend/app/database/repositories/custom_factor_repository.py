"""
CustomFactorRepository - Repository for CustomFactor model

Provides specialized queries for user-defined factors using the actual CustomFactor model.
"""

from typing import List, Optional
from datetime import datetime, timezone
from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.repositories.base import BaseRepository
from app.database.models.indicator import CustomFactor, FactorStatus


class CustomFactorRepository(BaseRepository[CustomFactor]):
    """
    Repository for CustomFactor operations.

    Provides specialized methods for:
    - User factor management
    - Publishing and sharing
    - Factor cloning
    - Usage tracking
    - Public factor discovery
    """

    def __init__(self, session: AsyncSession):
        """Initialize repository with CustomFactor model"""
        super().__init__(CustomFactor, session)

    async def get_user_factors(
        self,
        user_id: str,
        status: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[CustomFactor]:
        """
        获取用户的所有因子

        Args:
            user_id: 用户ID
            status: 因子状态过滤
            skip: 跳过记录数
            limit: 返回记录数

        Returns:
            用户因子列表
        """
        conditions = [
            self.model.user_id == user_id,
            self.model.is_deleted == False
        ]

        if status is not None:
            conditions.append(self.model.status == status)

        stmt = select(self.model).where(and_(*conditions)).order_by(
            self.model.created_at.desc()
        ).offset(skip).limit(limit)

        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_public_factors(
        self,
        skip: int = 0,
        limit: int = 20
    ) -> List[CustomFactor]:
        """
        获取所有公开的因子

        Args:
            skip: 跳过记录数
            limit: 返回记录数

        Returns:
            公开因子列表
        """
        stmt = select(self.model).where(
            and_(
                self.model.is_public == True,
                self.model.status == FactorStatus.PUBLISHED.value,
                self.model.is_deleted == False
            )
        ).order_by(
            self.model.usage_count.desc()
        ).offset(skip).limit(limit)

        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def publish_factor(self, factor_id: str) -> Optional[CustomFactor]:
        """
        发布因子

        Args:
            factor_id: 因子ID

        Returns:
            更新后的因子，如果因子不存在则返回None
        """
        factor = await self.get(factor_id)
        if not factor:
            return None

        factor.status = FactorStatus.PUBLISHED.value
        factor.published_at = datetime.now(timezone.utc)
        await self.session.commit()
        await self.session.refresh(factor)
        return factor

    async def make_public(self, factor_id: str) -> Optional[CustomFactor]:
        """
        将因子设为公开（必须先发布）

        Args:
            factor_id: 因子ID

        Returns:
            更新后的因子，如果因子不存在或未发布则返回None
        """
        factor = await self.get(factor_id)
        if not factor or factor.status != FactorStatus.PUBLISHED.value:
            return None

        factor.is_public = True
        factor.shared_at = datetime.now(timezone.utc)
        await self.session.commit()
        await self.session.refresh(factor)
        return factor

    async def clone_factor(
        self,
        factor_id: str,
        new_user_id: str,
        new_factor_name: Optional[str] = None
    ) -> Optional[CustomFactor]:
        """
        克隆因子到新用户

        Args:
            factor_id: 源因子ID
            new_user_id: 新用户ID
            new_factor_name: 新名称（可选，默认使用原名称）

        Returns:
            克隆后的新因子，如果源因子不存在则返回None
        """
        original = await self.get(factor_id)
        if not original:
            return None

        # Create cloned factor data
        cloned_data = {
            "factor_name": new_factor_name or original.factor_name,
            "user_id": new_user_id,
            "base_indicator_id": original.base_indicator_id,
            "formula": original.formula,
            "formula_language": original.formula_language,
            "description": original.description,
            "status": FactorStatus.DRAFT.value,  # Cloned factor starts as draft
            "is_public": False,
            "cloned_from_id": original.id
        }

        cloned = await self.create(cloned_data, commit=True)

        # Increment clone count of original
        original.clone_count += 1
        await self.session.commit()

        return cloned

    async def increment_usage_count(self, factor_id: str) -> bool:
        """
        原子性增加因子使用次数

        Args:
            factor_id: 因子ID

        Returns:
            是否成功
        """
        factor = await self.get(factor_id)
        if not factor:
            return False

        factor.usage_count += 1
        await self.session.commit()
        return True

    async def search_by_name(
        self,
        keyword: str,
        user_id: Optional[str] = None,
        skip: int = 0,
        limit: int = 20
    ) -> List[CustomFactor]:
        """
        按名称或描述搜索因子

        Args:
            keyword: 搜索关键词
            user_id: 用户ID（可选，仅搜索特定用户的因子）
            skip: 跳过记录数
            limit: 返回记录数

        Returns:
            匹配的因子列表
        """
        conditions = [
            or_(
                self.model.factor_name.like(f"%{keyword}%"),
                self.model.description.like(f"%{keyword}%")
            ),
            self.model.is_deleted == False
        ]

        if user_id:
            conditions.append(self.model.user_id == user_id)

        stmt = select(self.model).where(and_(*conditions)).order_by(
            self.model.usage_count.desc()
        ).offset(skip).limit(limit)

        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_popular_factors(
        self,
        limit: int = 10
    ) -> List[CustomFactor]:
        """
        获取热门公开因子

        Args:
            limit: 返回记录数

        Returns:
            热门因子列表
        """
        conditions = [
            self.model.is_deleted == False,
            self.model.status == FactorStatus.PUBLISHED.value,
            self.model.is_public == True,
            self.model.usage_count > 0
        ]

        stmt = select(self.model).where(and_(*conditions)).order_by(
            self.model.usage_count.desc()
        ).limit(limit)

        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_base_indicator(
        self,
        base_indicator_id: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[CustomFactor]:
        """
        按基础指标ID获取因子

        Args:
            base_indicator_id: 基础指标ID
            skip: 跳过记录数
            limit: 返回记录数

        Returns:
            使用该基础指标的因子列表
        """
        stmt = select(self.model).where(
            and_(
                self.model.base_indicator_id == base_indicator_id,
                self.model.is_deleted == False
            )
        ).order_by(
            self.model.created_at.desc()
        ).offset(skip).limit(limit)

        result = await self.session.execute(stmt)
        return list(result.scalars().all())
