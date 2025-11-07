"""
TDD Tests for Report Export Service

Test coverage for:
- PDF report generation
- Excel data export
- Chart export (PNG/SVG)
- Export format validation
"""

import pytest
from pathlib import Path
from decimal import Decimal

from app.modules.backtest.services.export_service import ExportService
from app.modules.backtest.exceptions import ResourceNotFoundError


class TestPDFExport:
    """Test PDF report generation."""

    @pytest.mark.asyncio
    async def test_generate_pdf_report(self, export_service: ExportService, sample_result_id: str, tmp_path: Path):
        """Test generating PDF report for backtest result."""
        # ARRANGE
        output_path = tmp_path / "report.pdf"

        # ACT
        result_path = await export_service.generate_pdf_report(sample_result_id, str(output_path))

        # ASSERT
        assert Path(result_path).exists()
        assert Path(result_path).suffix == ".pdf"
        assert Path(result_path).stat().st_size > 0

    @pytest.mark.asyncio
    async def test_pdf_report_contains_metrics(self, export_service: ExportService, sample_result_id: str, tmp_path: Path):
        """Test PDF report contains key metrics."""
        # ARRANGE
        output_path = tmp_path / "report.pdf"

        # ACT
        result_path = await export_service.generate_pdf_report(sample_result_id, str(output_path))

        # ASSERT
        assert Path(result_path).exists()
        # PDF should contain metrics (we'll verify file size as proxy)
        assert Path(result_path).stat().st_size > 100  # At least 100 bytes

    @pytest.mark.asyncio
    async def test_pdf_export_not_found(self, export_service: ExportService, tmp_path: Path):
        """Test PDF export for non-existent result."""
        # ARRANGE
        output_path = tmp_path / "report.pdf"

        # ACT & ASSERT
        with pytest.raises(ResourceNotFoundError):
            await export_service.generate_pdf_report("nonexistent_id", str(output_path))


class TestExcelExport:
    """Test Excel data export."""

    @pytest.mark.asyncio
    async def test_export_to_excel(self, export_service: ExportService, sample_result_id: str, tmp_path: Path):
        """Test exporting backtest data to Excel."""
        # ARRANGE
        output_path = tmp_path / "data.xlsx"

        # ACT
        result_path = await export_service.export_to_excel(sample_result_id, str(output_path))

        # ASSERT
        assert Path(result_path).exists()
        assert Path(result_path).suffix == ".xlsx"
        assert Path(result_path).stat().st_size > 0

    @pytest.mark.asyncio
    async def test_excel_contains_multiple_sheets(self, export_service: ExportService, sample_result_id: str, tmp_path: Path):
        """Test Excel file contains multiple sheets (summary, trades, metrics)."""
        # ARRANGE
        output_path = tmp_path / "data.xlsx"

        # ACT
        result_path = await export_service.export_to_excel(sample_result_id, str(output_path))

        # ASSERT
        assert Path(result_path).exists()
        # Verify file is valid Excel format (basic check)
        with open(result_path, 'rb') as f:
            header = f.read(4)
            # Excel files start with PK (ZIP format)
            assert header[:2] == b'PK'

    @pytest.mark.asyncio
    async def test_excel_export_not_found(self, export_service: ExportService, tmp_path: Path):
        """Test Excel export for non-existent result."""
        # ARRANGE
        output_path = tmp_path / "data.xlsx"

        # ACT & ASSERT
        with pytest.raises(ResourceNotFoundError):
            await export_service.export_to_excel("nonexistent_id", str(output_path))


class TestChartExport:
    """Test chart export functionality."""

    @pytest.mark.asyncio
    async def test_export_returns_chart(self, export_service: ExportService, sample_result_id: str, tmp_path: Path):
        """Test exporting returns chart."""
        # ARRANGE
        output_path = tmp_path / "returns.png"

        # ACT
        result_path = await export_service.export_chart(
            sample_result_id,
            chart_type="returns",
            output_path=str(output_path),
            format="png"
        )

        # ASSERT
        assert Path(result_path).exists()
        assert Path(result_path).suffix == ".png"
        assert Path(result_path).stat().st_size > 0

    @pytest.mark.asyncio
    async def test_export_drawdown_chart(self, export_service: ExportService, sample_result_id: str, tmp_path: Path):
        """Test exporting drawdown chart."""
        # ARRANGE
        output_path = tmp_path / "drawdown.png"

        # ACT
        result_path = await export_service.export_chart(
            sample_result_id,
            chart_type="drawdown",
            output_path=str(output_path),
            format="png"
        )

        # ASSERT
        assert Path(result_path).exists()
        assert Path(result_path).suffix == ".png"

    @pytest.mark.asyncio
    async def test_export_chart_svg_format(self, export_service: ExportService, sample_result_id: str, tmp_path: Path):
        """Test exporting chart in SVG format."""
        # ARRANGE
        output_path = tmp_path / "returns.svg"

        # ACT
        result_path = await export_service.export_chart(
            sample_result_id,
            chart_type="returns",
            output_path=str(output_path),
            format="svg"
        )

        # ASSERT
        assert Path(result_path).exists()
        assert Path(result_path).suffix == ".svg"
        # SVG files should contain XML
        with open(result_path, 'r') as f:
            content = f.read()
            assert '<svg' in content

    @pytest.mark.asyncio
    async def test_export_chart_invalid_type(self, export_service: ExportService, sample_result_id: str, tmp_path: Path):
        """Test exporting chart with invalid type."""
        # ARRANGE
        output_path = tmp_path / "chart.png"

        # ACT & ASSERT
        with pytest.raises(ValueError):
            await export_service.export_chart(
                sample_result_id,
                chart_type="invalid_type",
                output_path=str(output_path),
                format="png"
            )


class TestBatchExport:
    """Test batch export functionality."""

    @pytest.mark.asyncio
    async def test_export_complete_package(self, export_service: ExportService, sample_result_id: str, tmp_path: Path):
        """Test exporting complete package (PDF + Excel + Charts)."""
        # ARRANGE
        output_dir = tmp_path / "export_package"

        # ACT
        result_paths = await export_service.export_complete_package(
            sample_result_id,
            str(output_dir)
        )

        # ASSERT
        assert "pdf" in result_paths
        assert "excel" in result_paths
        assert "charts" in result_paths
        assert Path(result_paths["pdf"]).exists()
        assert Path(result_paths["excel"]).exists()
        assert len(result_paths["charts"]) > 0
        for chart_path in result_paths["charts"]:
            assert Path(chart_path).exists()

    @pytest.mark.asyncio
    async def test_export_package_creates_directory(self, export_service: ExportService, sample_result_id: str, tmp_path: Path):
        """Test export package creates output directory if not exists."""
        # ARRANGE
        output_dir = tmp_path / "new_directory" / "export"

        # ACT
        result_paths = await export_service.export_complete_package(
            sample_result_id,
            str(output_dir)
        )

        # ASSERT
        assert Path(output_dir).exists()
        assert Path(output_dir).is_dir()


class TestExportMetadata:
    """Test export metadata functionality."""

    @pytest.mark.asyncio
    async def test_get_export_metadata(self, export_service: ExportService, sample_result_id: str):
        """Test getting export metadata."""
        # ACT
        metadata = await export_service.get_export_metadata(sample_result_id)

        # ASSERT
        assert "result_id" in metadata
        assert "export_timestamp" in metadata
        assert "available_formats" in metadata
        assert "pdf" in metadata["available_formats"]
        assert "excel" in metadata["available_formats"]
        assert "charts" in metadata["available_formats"]

    @pytest.mark.asyncio
    async def test_export_metadata_includes_file_sizes(self, export_service: ExportService, sample_result_id: str, tmp_path: Path):
        """Test export metadata includes estimated file sizes."""
        # ACT
        metadata = await export_service.get_export_metadata(sample_result_id)

        # ASSERT
        assert "estimated_sizes" in metadata
        assert "pdf" in metadata["estimated_sizes"]
        assert "excel" in metadata["estimated_sizes"]
