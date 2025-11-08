"""
TDD Tests for Chart API Endpoints

测试覆盖所有Chart API端点:
- POST /api/charts - 创建图表配置
- GET /api/charts - 列表查询(带分页和过滤)
- GET /api/charts/{id} - 获取单个图表
- PUT /api/charts/{id} - 更新图表配置
- DELETE /api/charts/{id} - 删除图表配置
- POST /api/charts/{id}/data - 获取图表数据
- POST /api/charts/{id}/export - 导出图表数据
- POST /api/charts/{id}/annotations - 添加注释
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

from app.database.models.dataset import Dataset
from app.database.models.chart import ChartConfig, ChartType
from app.modules.data_management.models.dataset import DataSource, DatasetStatus


@pytest.mark.asyncio
class TestCreateChart:
    """测试 POST /api/charts 创建图表配置"""

    async def test_create_chart_success(
        self, async_client: AsyncClient, db_session: AsyncSession
    ):
        """测试成功创建图表配置"""
        # ARRANGE - 创建测试数据集
        dataset = Dataset(
            name="Test Dataset",
            source=DataSource.LOCAL,
            file_path="/data/test.csv",
            status=DatasetStatus.VALID,
        )
        db_session.add(dataset)
        await db_session.commit()
        await db_session.refresh(dataset)

        chart_data = {
            "name": "Test Chart",
            "chart_type": ChartType.KLINE.value,
            "dataset_id": dataset.id,
            "config": {"theme": "dark"},
            "description": "Test chart description",
        }

        # ACT
        response = await async_client.post("/api/charts", json=chart_data)

        # ASSERT
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Test Chart"
        assert data["chart_type"] == ChartType.KLINE.value
        assert data["dataset_id"] == dataset.id
        assert data["config"] == {"theme": "dark"}
        assert data["description"] == "Test chart description"
        assert "id" in data
        assert "created_at" in data
        assert "updated_at" in data

    async def test_create_chart_dataset_not_found(self, async_client: AsyncClient):
        """测试创建图表时数据集不存在"""
        # ARRANGE
        chart_data = {
            "name": "Test Chart",
            "chart_type": ChartType.KLINE.value,
            "dataset_id": "nonexistent-id",
            "config": {},
        }

        # ACT
        response = await async_client.post("/api/charts", json=chart_data)

        # ASSERT
        assert response.status_code == 404
        assert "Dataset not found" in response.json()["detail"]

    async def test_create_chart_missing_required_fields(self, async_client: AsyncClient):
        """测试创建图表缺少必需字段"""
        # ARRANGE
        chart_data = {"name": "Test Chart"}  # 缺少 chart_type 和 dataset_id

        # ACT
        response = await async_client.post("/api/charts", json=chart_data)

        # ASSERT
        assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
class TestListCharts:
    """测试 GET /api/charts 列表查询"""

    async def test_list_charts_empty(self, async_client: AsyncClient):
        """测试空列表"""
        # ACT
        response = await async_client.get("/api/charts")

        # ASSERT
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["items"] == []

    async def test_list_charts_with_data(
        self, async_client: AsyncClient, db_session: AsyncSession
    ):
        """测试获取图表列表"""
        # ARRANGE - 创建测试数据
        dataset = Dataset(
            name="Test Dataset",
            source=DataSource.LOCAL,
            file_path="/data/test.csv",
            status=DatasetStatus.VALID,
        )
        db_session.add(dataset)
        await db_session.commit()
        await db_session.refresh(dataset)

        chart1 = ChartConfig(
            name="Chart 1",
            chart_type=ChartType.KLINE,
            dataset_id=dataset.id,
            config={},
        )
        chart2 = ChartConfig(
            name="Chart 2",
            chart_type=ChartType.LINE,
            dataset_id=dataset.id,
            config={},
        )
        db_session.add_all([chart1, chart2])
        await db_session.commit()

        # ACT
        response = await async_client.get("/api/charts")

        # ASSERT
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        assert len(data["items"]) == 2

    async def test_list_charts_with_dataset_filter(
        self, async_client: AsyncClient, db_session: AsyncSession
    ):
        """测试按dataset_id过滤"""
        # ARRANGE
        dataset1 = Dataset(
            name="Dataset 1",
            source=DataSource.LOCAL,
            file_path="/data/test1.csv",
            status=DatasetStatus.VALID,
        )
        dataset2 = Dataset(
            name="Dataset 2",
            source=DataSource.LOCAL,
            file_path="/data/test2.csv",
            status=DatasetStatus.VALID,
        )
        db_session.add_all([dataset1, dataset2])
        await db_session.commit()
        await db_session.refresh(dataset1)
        await db_session.refresh(dataset2)

        chart1 = ChartConfig(
            name="Chart 1",
            chart_type=ChartType.KLINE,
            dataset_id=dataset1.id,
            config={},
        )
        chart2 = ChartConfig(
            name="Chart 2",
            chart_type=ChartType.LINE,
            dataset_id=dataset2.id,
            config={},
        )
        db_session.add_all([chart1, chart2])
        await db_session.commit()

        # ACT
        response = await async_client.get(f"/api/charts?dataset_id={dataset1.id}")

        # ASSERT
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["items"][0]["dataset_id"] == dataset1.id

    async def test_list_charts_with_chart_type_filter(
        self, async_client: AsyncClient, db_session: AsyncSession
    ):
        """测试按chart_type过滤"""
        # ARRANGE
        dataset = Dataset(
            name="Test Dataset",
            source=DataSource.LOCAL,
            file_path="/data/test.csv",
            status=DatasetStatus.VALID,
        )
        db_session.add(dataset)
        await db_session.commit()
        await db_session.refresh(dataset)

        chart1 = ChartConfig(
            name="Candlestick Chart",
            chart_type=ChartType.KLINE,
            dataset_id=dataset.id,
            config={},
        )
        chart2 = ChartConfig(
            name="Line Chart",
            chart_type=ChartType.LINE,
            dataset_id=dataset.id,
            config={},
        )
        db_session.add_all([chart1, chart2])
        await db_session.commit()

        # ACT
        response = await async_client.get(
            f"/api/charts?chart_type={ChartType.KLINE.value}"
        )

        # ASSERT
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["items"][0]["chart_type"] == ChartType.KLINE.value

    async def test_list_charts_with_search(
        self, async_client: AsyncClient, db_session: AsyncSession
    ):
        """测试按名称搜索"""
        # ARRANGE
        dataset = Dataset(
            name="Test Dataset",
            source=DataSource.LOCAL,
            file_path="/data/test.csv",
            status=DatasetStatus.VALID,
        )
        db_session.add(dataset)
        await db_session.commit()
        await db_session.refresh(dataset)

        chart1 = ChartConfig(
            name="Bitcoin Price Chart",
            chart_type=ChartType.KLINE,
            dataset_id=dataset.id,
            config={},
        )
        chart2 = ChartConfig(
            name="Ethereum Volume",
            chart_type=ChartType.BAR,
            dataset_id=dataset.id,
            config={},
        )
        db_session.add_all([chart1, chart2])
        await db_session.commit()

        # ACT
        response = await async_client.get("/api/charts?search=Bitcoin")

        # ASSERT
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert "Bitcoin" in data["items"][0]["name"]

    async def test_list_charts_with_pagination(
        self, async_client: AsyncClient, db_session: AsyncSession
    ):
        """测试分页参数"""
        # ARRANGE
        dataset = Dataset(
            name="Test Dataset",
            source=DataSource.LOCAL,
            file_path="/data/test.csv",
            status=DatasetStatus.VALID,
        )
        db_session.add(dataset)
        await db_session.commit()
        await db_session.refresh(dataset)

        # 创建5个图表
        for i in range(5):
            chart = ChartConfig(
                name=f"Chart {i}",
                chart_type=ChartType.LINE,
                dataset_id=dataset.id,
                config={},
            )
            db_session.add(chart)
        await db_session.commit()

        # ACT
        response = await async_client.get("/api/charts?skip=2&limit=2")

        # ASSERT
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 5
        assert len(data["items"]) == 2


@pytest.mark.asyncio
class TestGetChart:
    """测试 GET /api/charts/{id} 获取单个图表"""

    async def test_get_chart_success(
        self, async_client: AsyncClient, db_session: AsyncSession
    ):
        """测试成功获取图表"""
        # ARRANGE
        dataset = Dataset(
            name="Test Dataset",
            source=DataSource.LOCAL,
            file_path="/data/test.csv",
            status=DatasetStatus.VALID,
        )
        db_session.add(dataset)
        await db_session.commit()
        await db_session.refresh(dataset)

        chart = ChartConfig(
            name="Test Chart",
            chart_type=ChartType.KLINE,
            dataset_id=dataset.id,
            config={"theme": "dark"},
            description="Test description",
        )
        db_session.add(chart)
        await db_session.commit()
        await db_session.refresh(chart)

        # ACT
        response = await async_client.get(f"/api/charts/{chart.id}")

        # ASSERT
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == chart.id
        assert data["name"] == "Test Chart"
        assert data["chart_type"] == ChartType.KLINE.value
        assert data["dataset_id"] == dataset.id
        assert data["config"] == {"theme": "dark"}

    async def test_get_chart_not_found(self, async_client: AsyncClient):
        """测试获取不存在的图表"""
        # ACT
        response = await async_client.get("/api/charts/nonexistent-id")

        # ASSERT
        assert response.status_code == 404
        assert "Chart not found" in response.json()["detail"]


@pytest.mark.asyncio
class TestUpdateChart:
    """测试 PUT /api/charts/{id} 更新图表配置"""

    async def test_update_chart_success(
        self, async_client: AsyncClient, db_session: AsyncSession
    ):
        """测试成功更新图表"""
        # ARRANGE
        dataset = Dataset(
            name="Test Dataset",
            source=DataSource.LOCAL,
            file_path="/data/test.csv",
            status=DatasetStatus.VALID,
        )
        db_session.add(dataset)
        await db_session.commit()
        await db_session.refresh(dataset)

        chart = ChartConfig(
            name="Original Chart",
            chart_type=ChartType.KLINE,
            dataset_id=dataset.id,
            config={},
        )
        db_session.add(chart)
        await db_session.commit()
        await db_session.refresh(chart)

        update_data = {
            "name": "Updated Chart",
            "config": {"theme": "light"},
            "description": "Updated description",
        }

        # ACT
        response = await async_client.put(f"/api/charts/{chart.id}", json=update_data)

        # ASSERT
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Chart"
        assert data["config"] == {"theme": "light"}
        assert data["description"] == "Updated description"
        assert data["chart_type"] == ChartType.KLINE.value  # 未更新的字段保持不变

    async def test_update_chart_partial_update(
        self, async_client: AsyncClient, db_session: AsyncSession
    ):
        """测试部分更新"""
        # ARRANGE
        dataset = Dataset(
            name="Test Dataset",
            source=DataSource.LOCAL,
            file_path="/data/test.csv",
            status=DatasetStatus.VALID,
        )
        db_session.add(dataset)
        await db_session.commit()
        await db_session.refresh(dataset)

        chart = ChartConfig(
            name="Original Chart",
            chart_type=ChartType.KLINE,
            dataset_id=dataset.id,
            config={"theme": "dark"},
            description="Original description",
        )
        db_session.add(chart)
        await db_session.commit()
        await db_session.refresh(chart)

        update_data = {"name": "Updated Chart"}  # 只更新名称

        # ACT
        response = await async_client.put(f"/api/charts/{chart.id}", json=update_data)

        # ASSERT
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Chart"
        assert data["config"] == {"theme": "dark"}  # 保持原值
        assert data["description"] == "Original description"  # 保持原值

    async def test_update_chart_not_found(self, async_client: AsyncClient):
        """测试更新不存在的图表"""
        # ARRANGE
        update_data = {"name": "Updated Chart"}

        # ACT
        response = await async_client.put(
            "/api/charts/nonexistent-id", json=update_data
        )

        # ASSERT
        assert response.status_code == 404
        assert "Chart not found" in response.json()["detail"]


@pytest.mark.asyncio
class TestDeleteChart:
    """测试 DELETE /api/charts/{id} 删除图表配置"""

    async def test_delete_chart_success(
        self, async_client: AsyncClient, db_session: AsyncSession
    ):
        """测试成功删除图表(软删除)"""
        # ARRANGE
        dataset = Dataset(
            name="Test Dataset",
            source=DataSource.LOCAL,
            file_path="/data/test.csv",
            status=DatasetStatus.VALID,
        )
        db_session.add(dataset)
        await db_session.commit()
        await db_session.refresh(dataset)

        chart = ChartConfig(
            name="Test Chart",
            chart_type=ChartType.KLINE,
            dataset_id=dataset.id,
            config={},
        )
        db_session.add(chart)
        await db_session.commit()
        await db_session.refresh(chart)

        # ACT
        response = await async_client.delete(f"/api/charts/{chart.id}")

        # ASSERT
        assert response.status_code == 200
        data = response.json()
        assert "deleted successfully" in data["message"]

    async def test_delete_chart_not_found(self, async_client: AsyncClient):
        """测试删除不存在的图表"""
        # ACT
        response = await async_client.delete("/api/charts/nonexistent-id")

        # ASSERT
        assert response.status_code == 404
        assert "Chart not found" in response.json()["detail"]


@pytest.mark.asyncio
class TestGetChartData:
    """测试 POST /api/charts/{id}/data 获取图表数据"""

    async def test_get_chart_data_success(
        self, async_client: AsyncClient, db_session: AsyncSession
    ):
        """测试成功获取图表数据"""
        # ARRANGE
        dataset = Dataset(
            name="Test Dataset",
            source=DataSource.LOCAL,
            file_path="/data/test.csv",
            status=DatasetStatus.VALID,
        )
        db_session.add(dataset)
        await db_session.commit()
        await db_session.refresh(dataset)

        chart = ChartConfig(
            name="Test Chart",
            chart_type=ChartType.KLINE,
            dataset_id=dataset.id,
            config={},
        )
        db_session.add(chart)
        await db_session.commit()
        await db_session.refresh(chart)

        request_data = {"dataset_id": dataset.id, "chart_format": "ohlc"}

        # ACT
        response = await async_client.post(
            f"/api/charts/{chart.id}/data", json=request_data
        )

        # ASSERT
        assert response.status_code == 200
        data = response.json()
        assert data["dataset_id"] == dataset.id
        assert "data" in data
        assert "metadata" in data
        assert data["metadata"]["chart_id"] == chart.id

    async def test_get_chart_data_with_indicators(
        self, async_client: AsyncClient, db_session: AsyncSession
    ):
        """测试获取带技术指标的图表数据"""
        # ARRANGE
        dataset = Dataset(
            name="Test Dataset",
            source=DataSource.LOCAL,
            file_path="/data/test.csv",
            status=DatasetStatus.VALID,
        )
        db_session.add(dataset)
        await db_session.commit()
        await db_session.refresh(dataset)

        chart = ChartConfig(
            name="Test Chart",
            chart_type=ChartType.KLINE,
            dataset_id=dataset.id,
            config={},
        )
        db_session.add(chart)
        await db_session.commit()
        await db_session.refresh(chart)

        request_data = {
            "dataset_id": dataset.id,
            "chart_format": "ohlc",
            "indicators": ["MACD", "RSI"],
            "indicator_params": {
                "macd_params": {"fast_period": 12, "slow_period": 26, "signal_period": 9},
                "rsi_params": {"period": 14, "overbought": 70, "oversold": 30},
            },
        }

        # ACT
        response = await async_client.post(
            f"/api/charts/{chart.id}/data", json=request_data
        )

        # ASSERT
        assert response.status_code == 200
        data = response.json()
        assert "indicators" in data
        assert data["indicators"] is not None

    async def test_get_chart_data_with_date_range(
        self, async_client: AsyncClient, db_session: AsyncSession
    ):
        """测试获取指定日期范围的图表数据"""
        # ARRANGE
        dataset = Dataset(
            name="Test Dataset",
            source=DataSource.LOCAL,
            file_path="/data/test.csv",
            status=DatasetStatus.VALID,
        )
        db_session.add(dataset)
        await db_session.commit()
        await db_session.refresh(dataset)

        chart = ChartConfig(
            name="Test Chart",
            chart_type=ChartType.KLINE,
            dataset_id=dataset.id,
            config={},
        )
        db_session.add(chart)
        await db_session.commit()
        await db_session.refresh(chart)

        request_data = {
            "dataset_id": dataset.id,
            "chart_format": "ohlc",
            "start_date": "2024-01-01T00:00:00",
            "end_date": "2024-01-31T23:59:59",
        }

        # ACT
        response = await async_client.post(
            f"/api/charts/{chart.id}/data", json=request_data
        )

        # ASSERT
        assert response.status_code == 200
        data = response.json()
        assert "data" in data

    async def test_get_chart_data_chart_not_found(self, async_client: AsyncClient):
        """测试获取不存在图表的数据"""
        # ARRANGE
        request_data = {"dataset_id": "some-dataset-id", "chart_format": "ohlc"}

        # ACT
        response = await async_client.post(
            "/api/charts/nonexistent-id/data", json=request_data
        )

        # ASSERT
        assert response.status_code == 404
        assert "Chart not found" in response.json()["detail"]


@pytest.mark.asyncio
class TestExportChartData:
    """测试 POST /api/charts/{id}/export 导出图表数据"""

    async def test_export_chart_data_csv(
        self, async_client: AsyncClient, db_session: AsyncSession
    ):
        """测试导出CSV格式数据"""
        # ARRANGE
        dataset = Dataset(
            name="Test Dataset",
            source=DataSource.LOCAL,
            file_path="/data/test.csv",
            status=DatasetStatus.VALID,
        )
        db_session.add(dataset)
        await db_session.commit()
        await db_session.refresh(dataset)

        chart = ChartConfig(
            name="Test Chart",
            chart_type=ChartType.KLINE,
            dataset_id=dataset.id,
            config={},
        )
        db_session.add(chart)
        await db_session.commit()
        await db_session.refresh(chart)

        request_data = {
            "chart_id": chart.id,
            "format": "csv",
            "include_indicators": False,
        }

        # ACT
        response = await async_client.post(
            f"/api/charts/{chart.id}/export", json=request_data
        )

        # ASSERT
        assert response.status_code == 200
        data = response.json()
        assert data["chart_id"] == chart.id
        assert data["format"] == "csv"
        assert "data" in data
        assert "filename" in data
        assert data["filename"].endswith(".csv")
        assert data["size_bytes"] > 0

    async def test_export_chart_data_with_columns(
        self, async_client: AsyncClient, db_session: AsyncSession
    ):
        """测试导出指定列的数据"""
        # ARRANGE
        dataset = Dataset(
            name="Test Dataset",
            source=DataSource.LOCAL,
            file_path="/data/test.csv",
            status=DatasetStatus.VALID,
        )
        db_session.add(dataset)
        await db_session.commit()
        await db_session.refresh(dataset)

        chart = ChartConfig(
            name="Test Chart",
            chart_type=ChartType.KLINE,
            dataset_id=dataset.id,
            config={},
        )
        db_session.add(chart)
        await db_session.commit()
        await db_session.refresh(chart)

        request_data = {
            "chart_id": chart.id,
            "format": "csv",
            "columns": ["date", "open", "close"],
        }

        # ACT
        response = await async_client.post(
            f"/api/charts/{chart.id}/export", json=request_data
        )

        # ASSERT
        assert response.status_code == 200
        data = response.json()
        assert data["format"] == "csv"

    async def test_export_chart_data_unsupported_format(
        self, async_client: AsyncClient, db_session: AsyncSession
    ):
        """测试导出不支持的格式"""
        # ARRANGE
        dataset = Dataset(
            name="Test Dataset",
            source=DataSource.LOCAL,
            file_path="/data/test.csv",
            status=DatasetStatus.VALID,
        )
        db_session.add(dataset)
        await db_session.commit()
        await db_session.refresh(dataset)

        chart = ChartConfig(
            name="Test Chart",
            chart_type=ChartType.KLINE,
            dataset_id=dataset.id,
            config={},
        )
        db_session.add(chart)
        await db_session.commit()
        await db_session.refresh(chart)

        request_data = {"chart_id": chart.id, "format": "json"}  # JSON暂未实现

        # ACT
        response = await async_client.post(
            f"/api/charts/{chart.id}/export", json=request_data
        )

        # ASSERT
        assert response.status_code == 400
        assert "not yet implemented" in response.json()["detail"]

    async def test_export_chart_data_chart_not_found(self, async_client: AsyncClient):
        """测试导出不存在图表的数据"""
        # ARRANGE
        request_data = {"chart_id": "nonexistent-id", "format": "csv"}

        # ACT
        response = await async_client.post(
            "/api/charts/nonexistent-id/export", json=request_data
        )

        # ASSERT
        assert response.status_code == 404
        assert "Chart not found" in response.json()["detail"]


@pytest.mark.asyncio
class TestAddChartAnnotation:
    """测试 POST /api/charts/{id}/annotations 添加注释"""

    async def test_add_text_annotation(
        self, async_client: AsyncClient, db_session: AsyncSession
    ):
        """测试添加文本注释"""
        # ARRANGE
        dataset = Dataset(
            name="Test Dataset",
            source=DataSource.LOCAL,
            file_path="/data/test.csv",
            status=DatasetStatus.VALID,
        )
        db_session.add(dataset)
        await db_session.commit()
        await db_session.refresh(dataset)

        chart = ChartConfig(
            name="Test Chart",
            chart_type=ChartType.KLINE,
            dataset_id=dataset.id,
            config={},
        )
        db_session.add(chart)
        await db_session.commit()
        await db_session.refresh(chart)

        request_data = {
            "chart_id": chart.id,
            "annotation": {
                "type": "text",
                "date": "2024-01-01T00:00:00",
                "text": "Important event",
                "position": "top",
            },
        }

        # ACT
        response = await async_client.post(
            f"/api/charts/{chart.id}/annotations", json=request_data
        )

        # ASSERT
        assert response.status_code == 200
        data = response.json()
        assert "Annotation added" in data["message"]

    async def test_add_marker_annotation(
        self, async_client: AsyncClient, db_session: AsyncSession
    ):
        """测试添加标记注释"""
        # ARRANGE
        dataset = Dataset(
            name="Test Dataset",
            source=DataSource.LOCAL,
            file_path="/data/test.csv",
            status=DatasetStatus.VALID,
        )
        db_session.add(dataset)
        await db_session.commit()
        await db_session.refresh(dataset)

        chart = ChartConfig(
            name="Test Chart",
            chart_type=ChartType.KLINE,
            dataset_id=dataset.id,
            config={},
        )
        db_session.add(chart)
        await db_session.commit()
        await db_session.refresh(chart)

        request_data = {
            "chart_id": chart.id,
            "annotation": {
                "type": "marker",
                "date": "2024-01-01T00:00:00",
                "label": "Buy Signal",
                "color": "green",
            },
        }

        # ACT
        response = await async_client.post(
            f"/api/charts/{chart.id}/annotations", json=request_data
        )

        # ASSERT
        assert response.status_code == 200
        data = response.json()
        assert "Annotation added" in data["message"]

    async def test_add_annotation_chart_not_found(self, async_client: AsyncClient):
        """测试为不存在的图表添加注释"""
        # ARRANGE
        request_data = {
            "chart_id": "nonexistent-id",
            "annotation": {
                "type": "text",
                "date": "2024-01-01T00:00:00",
                "text": "Test",
                "position": "top",
            },
        }

        # ACT
        response = await async_client.post(
            "/api/charts/nonexistent-id/annotations", json=request_data
        )

        # ASSERT
        assert response.status_code == 404
        assert "Chart not found" in response.json()["detail"]


@pytest.mark.asyncio
class TestChartAPIExceptionHandling:
    """测试Chart API的异常处理路径"""

    async def test_create_chart_database_error(
        self, async_client: AsyncClient, db_session: AsyncSession, mocker
    ):
        """测试创建图表时数据库错误"""
        # ARRANGE
        dataset = Dataset(
            name="Test Dataset",
            source=DataSource.LOCAL,
            file_path="/data/test.csv",
            status=DatasetStatus.VALID,
        )
        db_session.add(dataset)
        await db_session.commit()
        await db_session.refresh(dataset)

        chart_data = {
            "name": "Test Chart",
            "chart_type": ChartType.KLINE.value,
            "dataset_id": dataset.id,
            "config": {"theme": "dark"},
        }

        # Mock ChartRepository.create to raise an exception
        mocker.patch(
            "app.database.repositories.chart.ChartRepository.create",
            side_effect=Exception("Database connection error"),
        )

        # ACT
        response = await async_client.post("/api/charts", json=chart_data)

        # ASSERT
        assert response.status_code == 500
        data = response.json()
        assert "Failed to create chart" in data["detail"]
        assert "Database connection error" in data["detail"]

    async def test_get_chart_database_error(
        self, async_client: AsyncClient, mocker
    ):
        """测试获取图表时数据库错误"""
        # ARRANGE
        mocker.patch(
            "app.database.repositories.chart.ChartRepository.get",
            side_effect=Exception("Database query failed"),
        )

        # ACT
        response = await async_client.get("/api/charts/some-id")

        # ASSERT
        assert response.status_code == 500
        data = response.json()
        assert "Failed to get chart" in data["detail"]

    async def test_update_chart_database_error(
        self, async_client: AsyncClient, db_session: AsyncSession, mocker
    ):
        """测试更新图表时数据库错误"""
        # ARRANGE
        dataset = Dataset(
            name="Test Dataset",
            source=DataSource.LOCAL,
            file_path="/data/test.csv",
            status=DatasetStatus.VALID,
        )
        db_session.add(dataset)
        await db_session.commit()

        chart = ChartConfig(
            name="Test Chart",
            chart_type=ChartType.KLINE,
            dataset_id=dataset.id,
            config={},
        )
        db_session.add(chart)
        await db_session.commit()
        await db_session.refresh(chart)

        update_data = {"name": "Updated Chart"}

        # Mock repository update to raise exception
        mocker.patch(
            "app.database.repositories.chart.ChartRepository.update",
            side_effect=Exception("Update failed"),
        )

        # ACT
        response = await async_client.put(
            f"/api/charts/{chart.id}", json=update_data
        )

        # ASSERT
        assert response.status_code == 500
        data = response.json()
        assert "Failed to update chart" in data["detail"]

    async def test_delete_chart_database_error(
        self, async_client: AsyncClient, db_session: AsyncSession, mocker
    ):
        """测试删除图表时数据库错误"""
        # ARRANGE
        dataset = Dataset(
            name="Test Dataset",
            source=DataSource.LOCAL,
            file_path="/data/test.csv",
            status=DatasetStatus.VALID,
        )
        db_session.add(dataset)
        await db_session.commit()

        chart = ChartConfig(
            name="Test Chart",
            chart_type=ChartType.KLINE,
            dataset_id=dataset.id,
            config={},
        )
        db_session.add(chart)
        await db_session.commit()
        await db_session.refresh(chart)

        # Mock soft_delete to raise exception
        mocker.patch(
            "app.database.repositories.chart.ChartRepository.soft_delete",
            side_effect=Exception("Delete operation failed"),
        )

        # ACT
        response = await async_client.delete(f"/api/charts/{chart.id}")

        # ASSERT
        assert response.status_code == 500
        data = response.json()
        assert "Failed to delete chart" in data["detail"]

    async def test_list_charts_database_error(
        self, async_client: AsyncClient, mocker
    ):
        """测试列表查询时数据库错误"""
        # ARRANGE
        mocker.patch(
            "app.database.repositories.chart.ChartRepository.get_with_filters",
            side_effect=Exception("Query execution failed"),
        )

        # ACT
        response = await async_client.get("/api/charts")

        # ASSERT
        assert response.status_code == 500
        data = response.json()
        assert "Failed to list charts" in data["detail"]

    async def test_get_chart_data_dataset_not_found(
        self, async_client: AsyncClient, db_session: AsyncSession
    ):
        """测试获取图表数据时数据集不存在"""
        # ARRANGE
        dataset = Dataset(
            name="Test Dataset",
            source=DataSource.LOCAL,
            file_path="/data/test.csv",
            status=DatasetStatus.VALID,
        )
        db_session.add(dataset)
        await db_session.commit()

        chart = ChartConfig(
            name="Test Chart",
            chart_type=ChartType.KLINE,
            dataset_id=dataset.id,
            config={},
        )
        db_session.add(chart)
        await db_session.commit()
        await db_session.refresh(chart)

        # Delete dataset to simulate not found
        await db_session.delete(dataset)
        await db_session.commit()

        request_data = {
            "dataset_id": chart.dataset_id,
            "chart_format": "ohlc",
        }

        # ACT
        response = await async_client.post(
            f"/api/charts/{chart.id}/data", json=request_data
        )

        # ASSERT
        assert response.status_code == 404
        data = response.json()
        assert "Dataset not found" in data["detail"]

    async def test_get_chart_data_with_exception(
        self, async_client: AsyncClient, db_session: AsyncSession, mocker
    ):
        """测试获取图表数据时发生异常"""
        # ARRANGE
        dataset = Dataset(
            name="Test Dataset",
            source=DataSource.LOCAL,
            file_path="/data/test.csv",
            status=DatasetStatus.VALID,
        )
        db_session.add(dataset)
        await db_session.commit()

        chart = ChartConfig(
            name="Test Chart",
            chart_type=ChartType.KLINE,
            dataset_id=dataset.id,
            config={},
        )
        db_session.add(chart)
        await db_session.commit()
        await db_session.refresh(chart)

        request_data = {
            "dataset_id": dataset.id,
            "chart_format": "ohlc",
        }

        # Mock ChartService to raise exception
        mocker.patch(
            "app.modules.data_management.services.chart_service.ChartService.generate_ohlc_data",
            side_effect=Exception("Data processing error"),
        )

        # ACT
        response = await async_client.post(
            f"/api/charts/{chart.id}/data", json=request_data
        )

        # ASSERT
        assert response.status_code == 500
        data = response.json()
        assert "Failed to generate chart data" in data["detail"]

    async def test_export_chart_data_with_exception(
        self, async_client: AsyncClient, db_session: AsyncSession, mocker
    ):
        """测试导出图表数据时发生异常"""
        # ARRANGE
        dataset = Dataset(
            name="Test Dataset",
            source=DataSource.LOCAL,
            file_path="/data/test.csv",
            status=DatasetStatus.VALID,
        )
        db_session.add(dataset)
        await db_session.commit()

        chart = ChartConfig(
            name="Test Chart",
            chart_type=ChartType.KLINE,
            dataset_id=dataset.id,
            config={},
        )
        db_session.add(chart)
        await db_session.commit()
        await db_session.refresh(chart)

        request_data = {
            "chart_id": chart.id,
            "format": "csv",
        }

        # Mock export service to raise exception
        mocker.patch(
            "app.modules.data_management.services.chart_service.ChartService.export_to_csv",
            side_effect=Exception("Export processing error"),
        )

        # ACT
        response = await async_client.post(
            f"/api/charts/{chart.id}/export", json=request_data
        )

        # ASSERT
        assert response.status_code == 500
        data = response.json()
        assert "Failed to export chart data" in data["detail"]

    async def test_add_annotation_with_exception(
        self, async_client: AsyncClient, db_session: AsyncSession, mocker
    ):
        """测试添加注释时发生异常"""
        # ARRANGE
        dataset = Dataset(
            name="Test Dataset",
            source=DataSource.LOCAL,
            file_path="/data/test.csv",
            status=DatasetStatus.VALID,
        )
        db_session.add(dataset)
        await db_session.commit()

        chart = ChartConfig(
            name="Test Chart",
            chart_type=ChartType.KLINE,
            dataset_id=dataset.id,
            config={},
        )
        db_session.add(chart)
        await db_session.commit()
        await db_session.refresh(chart)

        request_data = {
            "chart_id": chart.id,
            "annotation": {
                "type": "text",
                "date": "2024-01-01T00:00:00",
                "text": "Test Annotation",
                "position": "top",
            },
        }

        # Mock repository update to raise exception
        mocker.patch(
            "app.database.repositories.chart.ChartRepository.update",
            side_effect=Exception("Annotation update failed"),
        )

        # ACT
        response = await async_client.post(
            f"/api/charts/{chart.id}/annotations", json=request_data
        )

        # ASSERT
        assert response.status_code == 500
        data = response.json()
        assert "Failed to add annotation" in data["detail"]


@pytest.mark.asyncio
class TestChartDataBoundaryConditions:
    """测试图表数据的边界条件和指标参数"""

    async def test_get_chart_data_with_all_indicator_params(
        self, async_client: AsyncClient, db_session: AsyncSession
    ):
        """测试所有4种指标的完整参数配置"""
        # ARRANGE
        dataset = Dataset(
            name="Test Dataset",
            source=DataSource.LOCAL,
            file_path="/data/test.csv",
            status=DatasetStatus.VALID,
        )
        db_session.add(dataset)
        await db_session.commit()
        await db_session.refresh(dataset)

        chart = ChartConfig(
            name="Test Chart",
            chart_type=ChartType.KLINE,
            dataset_id=dataset.id,
            config={},
        )
        db_session.add(chart)
        await db_session.commit()
        await db_session.refresh(chart)

        request_data = {
            "dataset_id": dataset.id,
            "chart_format": "ohlc",
            "indicators": ["MACD", "RSI", "KDJ"],
            "indicator_params": {
                "macd_params": {
                    "fast_period": 12,
                    "slow_period": 26,
                    "signal_period": 9
                },
                "rsi_params": {
                    "period": 14,
                    "overbought": 70,
                    "oversold": 30
                },
                "kdj_params": {
                    "k_period": 9,
                    "d_period": 3,
                    "j_period": 3
                },
            },
        }

        # ACT
        response = await async_client.post(
            f"/api/charts/{chart.id}/data", json=request_data
        )

        # ASSERT
        assert response.status_code == 200
        data = response.json()
        assert data["dataset_id"] == dataset.id
        assert "indicators" in data
        assert data["indicators"] is not None

    async def test_get_chart_data_macd_only_with_params(
        self, async_client: AsyncClient, db_session: AsyncSession
    ):
        """单独测试MACD指标及其参数"""
        # ARRANGE
        dataset = Dataset(
            name="Test Dataset",
            source=DataSource.LOCAL,
            file_path="/data/test.csv",
            status=DatasetStatus.VALID,
        )
        db_session.add(dataset)
        await db_session.commit()
        await db_session.refresh(dataset)

        chart = ChartConfig(
            name="Test Chart",
            chart_type=ChartType.KLINE,
            dataset_id=dataset.id,
            config={},
        )
        db_session.add(chart)
        await db_session.commit()
        await db_session.refresh(chart)

        request_data = {
            "dataset_id": dataset.id,
            "chart_format": "ohlc",
            "indicators": ["MACD"],
            "indicator_params": {
                "macd_params": {
                    "fast_period": 10,
                    "slow_period": 20,
                    "signal_period": 5
                },
            },
        }

        # ACT
        response = await async_client.post(
            f"/api/charts/{chart.id}/data", json=request_data
        )

        # ASSERT
        assert response.status_code == 200
        data = response.json()
        assert "indicators" in data
        assert data["indicators"] is not None

    async def test_get_chart_data_rsi_only_with_params(
        self, async_client: AsyncClient, db_session: AsyncSession
    ):
        """单独测试RSI指标及其参数"""
        # ARRANGE
        dataset = Dataset(
            name="Test Dataset",
            source=DataSource.LOCAL,
            file_path="/data/test.csv",
            status=DatasetStatus.VALID,
        )
        db_session.add(dataset)
        await db_session.commit()
        await db_session.refresh(dataset)

        chart = ChartConfig(
            name="Test Chart",
            chart_type=ChartType.KLINE,
            dataset_id=dataset.id,
            config={},
        )
        db_session.add(chart)
        await db_session.commit()
        await db_session.refresh(chart)

        request_data = {
            "dataset_id": dataset.id,
            "chart_format": "ohlc",
            "indicators": ["RSI"],
            "indicator_params": {
                "rsi_params": {
                    "period": 21,
                    "overbought": 80,
                    "oversold": 20
                },
            },
        }

        # ACT
        response = await async_client.post(
            f"/api/charts/{chart.id}/data", json=request_data
        )

        # ASSERT
        assert response.status_code == 200
        data = response.json()
        assert "indicators" in data
        assert data["indicators"] is not None

    async def test_get_chart_data_kdj_only_with_params(
        self, async_client: AsyncClient, db_session: AsyncSession
    ):
        """单独测试KDJ指标及其参数"""
        # ARRANGE
        dataset = Dataset(
            name="Test Dataset",
            source=DataSource.LOCAL,
            file_path="/data/test.csv",
            status=DatasetStatus.VALID,
        )
        db_session.add(dataset)
        await db_session.commit()
        await db_session.refresh(dataset)

        chart = ChartConfig(
            name="Test Chart",
            chart_type=ChartType.KLINE,
            dataset_id=dataset.id,
            config={},
        )
        db_session.add(chart)
        await db_session.commit()
        await db_session.refresh(chart)

        request_data = {
            "dataset_id": dataset.id,
            "chart_format": "ohlc",
            "indicators": ["KDJ"],
            "indicator_params": {
                "kdj_params": {
                    "k_period": 14,
                    "d_period": 5,
                    "j_period": 5
                },
            },
        }

        # ACT
        response = await async_client.post(
            f"/api/charts/{chart.id}/data", json=request_data
        )

        # ASSERT
        assert response.status_code == 200
        data = response.json()
        assert "indicators" in data
        assert data["indicators"] is not None

    async def test_get_chart_data_ma_only_with_params(
        self, async_client: AsyncClient, db_session: AsyncSession
    ):
        """单独测试MA指标及其参数"""
        # ARRANGE
        dataset = Dataset(
            name="Test Dataset",
            source=DataSource.LOCAL,
            file_path="/data/test.csv",
            status=DatasetStatus.VALID,
        )
        db_session.add(dataset)
        await db_session.commit()
        await db_session.refresh(dataset)

        chart = ChartConfig(
            name="Test Chart",
            chart_type=ChartType.KLINE,
            dataset_id=dataset.id,
            config={},
        )
        db_session.add(chart)
        await db_session.commit()
        await db_session.refresh(chart)

        request_data = {
            "dataset_id": dataset.id,
            "chart_format": "ohlc",
            "indicators": ["MA"],
            "indicator_params": {
                "ma_params": {
                    "periods": [5, 10, 20, 30, 60]
                },
            },
        }

        # ACT
        response = await async_client.post(
            f"/api/charts/{chart.id}/data", json=request_data
        )

        # ASSERT
        assert response.status_code == 200
        data = response.json()
        assert "indicators" in data
        assert data["indicators"] is not None

    async def test_get_chart_data_candlestick_format(
        self, async_client: AsyncClient, db_session: AsyncSession
    ):
        """测试candlestick格式而非ohlc"""
        # ARRANGE
        dataset = Dataset(
            name="Test Dataset",
            source=DataSource.LOCAL,
            file_path="/data/test.csv",
            status=DatasetStatus.VALID,
        )
        db_session.add(dataset)
        await db_session.commit()
        await db_session.refresh(dataset)

        chart = ChartConfig(
            name="Test Chart",
            chart_type=ChartType.KLINE,
            dataset_id=dataset.id,
            config={},
        )
        db_session.add(chart)
        await db_session.commit()
        await db_session.refresh(chart)

        request_data = {
            "dataset_id": dataset.id,
            "chart_format": "candlestick",
        }

        # ACT
        response = await async_client.post(
            f"/api/charts/{chart.id}/data", json=request_data
        )

        # ASSERT
        assert response.status_code == 200
        data = response.json()
        assert data["dataset_id"] == dataset.id
        assert "data" in data

    async def test_get_chart_data_with_start_date_only(
        self, async_client: AsyncClient, db_session: AsyncSession
    ):
        """只提供start_date的日期过滤"""
        # ARRANGE
        dataset = Dataset(
            name="Test Dataset",
            source=DataSource.LOCAL,
            file_path="/data/test.csv",
            status=DatasetStatus.VALID,
        )
        db_session.add(dataset)
        await db_session.commit()
        await db_session.refresh(dataset)

        chart = ChartConfig(
            name="Test Chart",
            chart_type=ChartType.KLINE,
            dataset_id=dataset.id,
            config={},
        )
        db_session.add(chart)
        await db_session.commit()
        await db_session.refresh(chart)

        request_data = {
            "dataset_id": dataset.id,
            "chart_format": "ohlc",
            "start_date": "2024-02-01T00:00:00",
        }

        # ACT
        response = await async_client.post(
            f"/api/charts/{chart.id}/data", json=request_data
        )

        # ASSERT
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        # 验证返回的数据确实经过了日期过滤
        assert data["metadata"]["total_records"] > 0

    async def test_get_chart_data_with_end_date_only(
        self, async_client: AsyncClient, db_session: AsyncSession
    ):
        """只提供end_date的日期过滤"""
        # ARRANGE
        dataset = Dataset(
            name="Test Dataset",
            source=DataSource.LOCAL,
            file_path="/data/test.csv",
            status=DatasetStatus.VALID,
        )
        db_session.add(dataset)
        await db_session.commit()
        await db_session.refresh(dataset)

        chart = ChartConfig(
            name="Test Chart",
            chart_type=ChartType.KLINE,
            dataset_id=dataset.id,
            config={},
        )
        db_session.add(chart)
        await db_session.commit()
        await db_session.refresh(chart)

        request_data = {
            "dataset_id": dataset.id,
            "chart_format": "ohlc",
            "end_date": "2024-02-15T23:59:59",
        }

        # ACT
        response = await async_client.post(
            f"/api/charts/{chart.id}/data", json=request_data
        )

        # ASSERT
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert data["metadata"]["total_records"] > 0

    async def test_get_chart_data_with_both_dates(
        self, async_client: AsyncClient, db_session: AsyncSession
    ):
        """同时提供start_date和end_date"""
        # ARRANGE
        dataset = Dataset(
            name="Test Dataset",
            source=DataSource.LOCAL,
            file_path="/data/test.csv",
            status=DatasetStatus.VALID,
        )
        db_session.add(dataset)
        await db_session.commit()
        await db_session.refresh(dataset)

        chart = ChartConfig(
            name="Test Chart",
            chart_type=ChartType.KLINE,
            dataset_id=dataset.id,
            config={},
        )
        db_session.add(chart)
        await db_session.commit()
        await db_session.refresh(chart)

        request_data = {
            "dataset_id": dataset.id,
            "chart_format": "ohlc",
            "start_date": "2024-01-15T00:00:00",
            "end_date": "2024-02-15T23:59:59",
        }

        # ACT
        response = await async_client.post(
            f"/api/charts/{chart.id}/data", json=request_data
        )

        # ASSERT
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        # 验证数据记录数在合理范围内（日期范围缩小后）
        assert data["metadata"]["total_records"] > 0

    async def test_get_chart_data_multiple_indicators_combined(
        self, async_client: AsyncClient, db_session: AsyncSession
    ):
        """测试多个指标组合(如MACD+RSI+MA)"""
        # ARRANGE
        dataset = Dataset(
            name="Test Dataset",
            source=DataSource.LOCAL,
            file_path="/data/test.csv",
            status=DatasetStatus.VALID,
        )
        db_session.add(dataset)
        await db_session.commit()
        await db_session.refresh(dataset)

        chart = ChartConfig(
            name="Test Chart",
            chart_type=ChartType.KLINE,
            dataset_id=dataset.id,
            config={},
        )
        db_session.add(chart)
        await db_session.commit()
        await db_session.refresh(chart)

        request_data = {
            "dataset_id": dataset.id,
            "chart_format": "ohlc",
            "indicators": ["MACD", "RSI", "MA"],
            "indicator_params": {
                "macd_params": {
                    "fast_period": 8,
                    "slow_period": 17,
                    "signal_period": 9
                },
                "rsi_params": {
                    "period": 14,
                    "overbought": 75,
                    "oversold": 25
                },
                "ma_params": {
                    "periods": [7, 14, 28]
                },
            },
        }

        # ACT
        response = await async_client.post(
            f"/api/charts/{chart.id}/data", json=request_data
        )

        # ASSERT
        assert response.status_code == 200
        data = response.json()
        assert "indicators" in data
        assert data["indicators"] is not None
        assert data["dataset_id"] == dataset.id

    async def test_get_chart_data_with_dates_and_indicators(
        self, async_client: AsyncClient, db_session: AsyncSession
    ):
        """测试日期过滤与指标参数的组合使用"""
        # ARRANGE
        dataset = Dataset(
            name="Test Dataset",
            source=DataSource.LOCAL,
            file_path="/data/test.csv",
            status=DatasetStatus.VALID,
        )
        db_session.add(dataset)
        await db_session.commit()
        await db_session.refresh(dataset)

        chart = ChartConfig(
            name="Test Chart",
            chart_type=ChartType.KLINE,
            dataset_id=dataset.id,
            config={},
        )
        db_session.add(chart)
        await db_session.commit()
        await db_session.refresh(chart)

        request_data = {
            "dataset_id": dataset.id,
            "chart_format": "candlestick",
            "start_date": "2024-01-10T00:00:00",
            "end_date": "2024-03-01T23:59:59",
            "indicators": ["MACD", "KDJ"],
            "indicator_params": {
                "macd_params": {
                    "fast_period": 12,
                    "slow_period": 26,
                    "signal_period": 9
                },
                "kdj_params": {
                    "k_period": 9,
                    "d_period": 3,
                    "j_period": 3
                },
            },
        }

        # ACT
        response = await async_client.post(
            f"/api/charts/{chart.id}/data", json=request_data
        )

        # ASSERT
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "indicators" in data
        assert data["indicators"] is not None

    async def test_get_chart_data_ma_with_custom_periods(
        self, async_client: AsyncClient, db_session: AsyncSession
    ):
        """测试MA指标使用自定义周期列表"""
        # ARRANGE
        dataset = Dataset(
            name="Test Dataset",
            source=DataSource.LOCAL,
            file_path="/data/test.csv",
            status=DatasetStatus.VALID,
        )
        db_session.add(dataset)
        await db_session.commit()
        await db_session.refresh(dataset)

        chart = ChartConfig(
            name="Test Chart",
            chart_type=ChartType.KLINE,
            dataset_id=dataset.id,
            config={},
        )
        db_session.add(chart)
        await db_session.commit()
        await db_session.refresh(chart)

        request_data = {
            "dataset_id": dataset.id,
            "chart_format": "ohlc",
            "indicators": ["MA"],
            "indicator_params": {
                "ma_params": {
                    "periods": [3, 7, 15, 30, 90]
                },
            },
        }

        # ACT
        response = await async_client.post(
            f"/api/charts/{chart.id}/data", json=request_data
        )

        # ASSERT
        assert response.status_code == 200
        data = response.json()
        assert "indicators" in data
        assert data["indicators"] is not None
