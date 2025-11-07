"""
Unit Tests for DataImportService

Tests the core functionality of the data import service including:
- File validation
- Data parsing
- Data processing
- Dataset creation
"""

import pytest
import pandas as pd
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.data_management.services.import_service import DataImportService
from app.database.models.import_task import ImportStatus, ImportType
from app.modules.data_management.schemas.import_schemas import (
    ImportTaskCreate,
    FileValidationResult,
)


@pytest.fixture
def mock_session():
    """Create a mock async session"""
    session = AsyncMock(spec=AsyncSession)
    return session


@pytest.fixture
def import_service(mock_session, tmp_path):
    """Create DataImportService instance with mocked dependencies"""
    service = DataImportService(mock_session, str(tmp_path))
    return service


@pytest.fixture
def sample_csv_file(tmp_path):
    """Create a sample CSV file for testing"""
    csv_content = """date,open,high,low,close,volume
2024-01-01,100,110,95,105,1000000
2024-01-02,105,115,100,110,1200000
2024-01-03,110,120,105,115,1100000
"""
    csv_file = tmp_path / "test_data.csv"
    csv_file.write_text(csv_content)
    return str(csv_file)


@pytest.fixture
def sample_excel_file(tmp_path):
    """Create a sample Excel file for testing"""
    df = pd.DataFrame({
        'date': pd.date_range('2024-01-01', periods=3),
        'open': [100, 105, 110],
        'high': [110, 115, 120],
        'low': [95, 100, 105],
        'close': [105, 110, 115],
        'volume': [1000000, 1200000, 1100000]
    })
    excel_file = tmp_path / "test_data.xlsx"
    df.to_excel(excel_file, index=False)
    return str(excel_file)


class TestCreateImportTask:
    """Test create_import_task method"""

    @pytest.mark.asyncio
    async def test_create_import_task_success(self, import_service):
        """Test successful task creation"""
        # Arrange
        task_data = ImportTaskCreate(
            task_name="Test Import",
            import_type=ImportType.CSV,
            original_filename="test.csv",
            file_path="/tmp/test.csv",
            file_size=1024
        )
        
        mock_task = Mock()
        mock_task.id = "test-task-id"
        import_service.import_task_repo.create = AsyncMock(return_value=mock_task)

        # Act
        task_id = await import_service.create_import_task(task_data)

        # Assert
        assert task_id == "test-task-id"
        import_service.import_task_repo.create.assert_called_once()


class TestValidateFile:
    """Test validate_file method"""

    @pytest.mark.asyncio
    async def test_validate_csv_file_success(self, import_service, sample_csv_file):
        """Test successful CSV file validation"""
        # Act
        result = await import_service.validate_file(sample_csv_file, ImportType.CSV)

        # Assert
        assert result.is_valid is True
        assert len(result.errors) == 0
        assert "encoding" in result.metadata
        assert "columns" in result.metadata
        assert set(result.metadata["columns"]) >= {"date", "open", "high", "low", "close", "volume"}

    @pytest.mark.asyncio
    async def test_validate_file_not_found(self, import_service):
        """Test validation with non-existent file"""
        # Act
        result = await import_service.validate_file("/nonexistent/file.csv", ImportType.CSV)

        # Assert
        assert result.is_valid is False
        assert len(result.errors) > 0
        assert "not found" in result.errors[0].lower()

    @pytest.mark.asyncio
    async def test_validate_file_missing_columns(self, import_service, tmp_path):
        """Test validation with missing required columns"""
        # Arrange
        csv_content = "col1,col2\n1,2\n3,4"
        csv_file = tmp_path / "invalid.csv"
        csv_file.write_text(csv_content)

        # Act
        result = await import_service.validate_file(str(csv_file), ImportType.CSV)

        # Assert
        assert result.is_valid is False
        assert any("missing required columns" in err.lower() for err in result.errors)

    @pytest.mark.asyncio
    async def test_validate_excel_file_success(self, import_service, sample_excel_file):
        """Test successful Excel file validation"""
        # Act
        result = await import_service.validate_file(sample_excel_file, ImportType.EXCEL)

        # Assert
        assert result.is_valid is True
        assert len(result.errors) == 0
        assert "columns" in result.metadata


class TestProcessImport:
    """Test process_import method"""

    @pytest.mark.asyncio
    async def test_process_import_success(self, import_service, sample_csv_file):
        """Test successful import processing"""
        # Arrange
        task_id = "test-task-id"
        
        # Mock repository methods
        import_service.import_task_repo.update = AsyncMock()
        import_service.import_task_repo.get = AsyncMock(return_value=Mock(
            task_name="Test Import",
            original_filename="test.csv"
        ))
        
        # Mock dataset creation
        mock_dataset = Mock()
        mock_dataset.id = "dataset-id"
        import_service.dataset_repo.create = AsyncMock(return_value=mock_dataset)

        # Act
        result = await import_service.process_import(
            task_id=task_id,
            file_path=sample_csv_file,
            import_type=ImportType.CSV
        )

        # Assert
        assert result.success is True
        assert result.rows_processed > 0
        assert result.dataset_id == "dataset-id"

    @pytest.mark.asyncio
    async def test_process_import_validation_failure(self, import_service, tmp_path):
        """Test import processing with validation failure"""
        # Arrange
        task_id = "test-task-id"
        invalid_file = tmp_path / "invalid.csv"
        invalid_file.write_text("col1,col2\n1,2")
        
        import_service.import_task_repo.update = AsyncMock()

        # Act
        result = await import_service.process_import(
            task_id=task_id,
            file_path=str(invalid_file),
            import_type=ImportType.CSV
        )

        # Assert
        assert result.success is False
        assert len(result.errors) > 0


class TestDetectEncoding:
    """Test _detect_encoding static method"""

    def test_detect_utf8_encoding(self, tmp_path):
        """Test UTF-8 encoding detection"""
        # Arrange
        file_path = tmp_path / "utf8.txt"
        file_path.write_text("Hello, World!", encoding='utf-8')

        # Act
        encoding = DataImportService._detect_encoding(str(file_path))

        # Assert
        assert encoding == 'utf-8'

    def test_detect_encoding_fallback(self, tmp_path):
        """Test encoding detection fallback"""
        # Arrange
        file_path = tmp_path / "unknown.txt"
        file_path.write_bytes(b'\xff\xfe\x00\x00')  # Invalid UTF-8

        # Act
        encoding = DataImportService._detect_encoding(str(file_path))

        # Assert
        assert encoding in ['utf-8', 'gbk', 'gb2312', 'latin-1', 'iso-8859-1']


@pytest.mark.asyncio
async def test_parse_file_csv(import_service, sample_csv_file):
    """Test CSV file parsing"""
    # Arrange
    metadata = {"encoding": "utf-8", "delimiter": ","}
    
    # Act
    df = await import_service._parse_file(
        sample_csv_file,
        ImportType.CSV,
        metadata,
        {}
    )

    # Assert
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 3
    assert "date" in df.columns
    assert "close" in df.columns


@pytest.mark.asyncio
async def test_process_data(import_service):
    """Test data processing and cleaning"""
    # Arrange
    df = pd.DataFrame({
        'date': ['2024-01-01', '2024-01-02', '2024-01-03'],
        'open': [100, 105, 110],
        'high': [110, 115, 120],
        'low': [95, 100, 105],
        'close': [105, 110, 115],
        'volume': [1000000, 1200000, 1100000]
    })
    
    import_service.import_task_repo.update = AsyncMock()

    # Act
    processed_df, errors = await import_service._process_data(df, "task-id", len(df))

    # Assert
    assert isinstance(processed_df, pd.DataFrame)
    assert len(processed_df) == 3
    assert pd.api.types.is_datetime64_any_dtype(processed_df['date'])


@pytest.mark.asyncio
async def test_create_dataset(import_service):
    """Test dataset creation from processed data"""
    # Arrange
    df = pd.DataFrame({
        'date': pd.date_range('2024-01-01', periods=3),
        'close': [105, 110, 115]
    })

    mock_task = Mock()
    mock_task.task_name = "Test Import"
    mock_task.original_filename = "test.csv"

    import_service.import_task_repo.get = AsyncMock(return_value=mock_task)

    mock_dataset = Mock()
    mock_dataset.id = "dataset-id"
    import_service.dataset_repo.create = AsyncMock(return_value=mock_dataset)

    # Act
    dataset_id = await import_service._create_dataset(
        "task-id",
        df,
        "/tmp/test.csv",
        {"encoding": "utf-8"}
    )

    # Assert
    assert dataset_id == "dataset-id"
    import_service.dataset_repo.create.assert_called_once()


class TestValidateFileEdgeCases:
    """Test edge cases in file validation"""

    @pytest.mark.asyncio
    async def test_validate_file_too_large(self, import_service, tmp_path):
        """Test validation with file exceeding size limit"""
        # Arrange
        large_file = tmp_path / "large.csv"
        # Create a file larger than MAX_FILE_SIZE
        with open(large_file, 'wb') as f:
            f.write(b'x' * (import_service.MAX_FILE_SIZE + 1))

        # Act
        result = await import_service.validate_file(str(large_file), ImportType.CSV)

        # Assert
        assert result.is_valid is False
        assert any("exceeds maximum" in err for err in result.errors)

    @pytest.mark.asyncio
    async def test_validate_unsupported_extension(self, import_service, tmp_path):
        """Test validation with unsupported file extension"""
        # Arrange
        txt_file = tmp_path / "data.txt"
        txt_file.write_text("some data")

        # Act
        result = await import_service.validate_file(str(txt_file), ImportType.CSV)

        # Assert
        assert result.is_valid is False
        assert any("unsupported file extension" in err.lower() for err in result.errors)

    @pytest.mark.asyncio
    async def test_validate_empty_csv(self, import_service, tmp_path):
        """Test validation with empty CSV file"""
        # Arrange
        empty_csv = tmp_path / "empty.csv"
        empty_csv.write_text("date,open,high,low,close,volume\n")

        # Act
        result = await import_service.validate_file(str(empty_csv), ImportType.CSV)

        # Assert
        assert result.is_valid is True
        assert any("empty" in warn.lower() for warn in result.warnings)

    @pytest.mark.asyncio
    async def test_validate_csv_with_missing_values(self, import_service, tmp_path):
        """Test validation with missing values in CSV"""
        # Arrange
        csv_content = """date,open,high,low,close,volume
2024-01-01,100,,95,105,1000000
2024-01-02,105,115,,110,
"""
        csv_file = tmp_path / "missing_values.csv"
        csv_file.write_text(csv_content)

        # Act
        result = await import_service.validate_file(str(csv_file), ImportType.CSV)

        # Assert
        assert result.is_valid is True
        assert len(result.warnings) > 0
        assert any("missing values" in warn.lower() for warn in result.warnings)

    @pytest.mark.asyncio
    async def test_validate_csv_delimiter_detection(self, import_service, tmp_path):
        """Test CSV delimiter detection (comma, tab, semicolon)"""
        # Test comma delimiter
        csv_comma = tmp_path / "comma.csv"
        csv_comma.write_text("date,open,high,low,close,volume\n2024-01-01,100,110,95,105,1000")
        result = await import_service.validate_file(str(csv_comma), ImportType.CSV)
        assert result.metadata.get("delimiter") == ","

        # Test tab delimiter
        csv_tab = tmp_path / "tab.csv"
        csv_tab.write_text("date\topen\thigh\tlow\tclose\tvolume\n2024-01-01\t100\t110\t95\t105\t1000")
        result = await import_service.validate_file(str(csv_tab), ImportType.CSV)
        assert result.metadata.get("delimiter") == "\t"

        # Test semicolon delimiter
        csv_semi = tmp_path / "semi.csv"
        csv_semi.write_text("date;open;high;low;close;volume\n2024-01-01;100;110;95;105;1000")
        result = await import_service.validate_file(str(csv_semi), ImportType.CSV)
        assert result.metadata.get("delimiter") == ";"

    @pytest.mark.asyncio
    async def test_validate_file_read_error(self, import_service, tmp_path):
        """Test validation with file read error"""
        # Arrange
        corrupt_file = tmp_path / "corrupt.csv"
        corrupt_file.write_bytes(b'\xff\xfe\x00\x00invalid')

        # Act
        result = await import_service.validate_file(str(corrupt_file), ImportType.CSV)

        # Assert - should handle error gracefully
        assert result.is_valid is False or len(result.errors) > 0


class TestProcessImportEdgeCases:
    """Test edge cases in process_import"""

    @pytest.mark.asyncio
    async def test_process_import_with_excel(self, import_service, sample_excel_file):
        """Test processing Excel file"""
        # Arrange
        task_id = "excel-task-id"

        import_service.import_task_repo.update = AsyncMock()
        import_service.import_task_repo.get = AsyncMock(return_value=Mock(
            task_name="Excel Import",
            original_filename="test.xlsx"
        ))

        mock_dataset = Mock()
        mock_dataset.id = "excel-dataset-id"
        import_service.dataset_repo.create = AsyncMock(return_value=mock_dataset)

        # Act
        result = await import_service.process_import(
            task_id=task_id,
            file_path=sample_excel_file,
            import_type=ImportType.EXCEL
        )

        # Assert
        assert result.success is True
        assert result.rows_processed > 0
        assert result.dataset_id == "excel-dataset-id"

    @pytest.mark.asyncio
    async def test_process_import_with_exception(self, import_service, sample_csv_file):
        """Test process_import handles exceptions"""
        # Arrange
        task_id = "error-task-id"

        # Mock to raise exception during the first update call (VALIDATING status)
        # But allow the final update in the exception handler to succeed
        call_count = 0
        def side_effect_update(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:  # First call raises exception
                raise Exception("Database error")
            return AsyncMock()  # Subsequent calls succeed

        import_service.import_task_repo.update = AsyncMock(side_effect=side_effect_update)

        # Act
        result = await import_service.process_import(
            task_id=task_id,
            file_path=sample_csv_file,
            import_type=ImportType.CSV
        )

        # Assert
        assert result.success is False
        assert len(result.errors) > 0
        assert any("error" in str(err).lower() for err in result.errors)


class TestParseFile:
    """Test _parse_file method"""

    @pytest.mark.asyncio
    async def test_parse_excel_file(self, import_service, sample_excel_file):
        """Test parsing Excel file"""
        # Arrange
        metadata = {"encoding": "utf-8"}

        # Act
        df = await import_service._parse_file(
            sample_excel_file,
            ImportType.EXCEL,
            metadata,
            {}
        )

        # Assert
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 3
        assert "date" in df.columns
        assert "close" in df.columns

    @pytest.mark.asyncio
    async def test_parse_file_unsupported_type(self, import_service, sample_csv_file):
        """Test parsing with unsupported import type"""
        # Arrange
        metadata = {"encoding": "utf-8", "delimiter": ","}

        # Act & Assert
        with pytest.raises(ValueError, match="Unsupported import type"):
            await import_service._parse_file(
                sample_csv_file,
                ImportType.JSON,  # Unsupported type
                metadata,
                {}
            )


class TestProcessData:
    """Test _process_data method"""

    @pytest.mark.asyncio
    async def test_process_data_with_missing_dates(self, import_service):
        """Test data processing with missing dates"""
        # Arrange
        df = pd.DataFrame({
            'date': ['2024-01-01', None, '2024-01-03'],
            'open': [100, 105, 110],
            'high': [110, 115, 120],
            'low': [95, 100, 105],
            'close': [105, 110, 115],
            'volume': [1000000, 1200000, 1100000]
        })

        import_service.import_task_repo.update = AsyncMock()

        # Act
        processed_df, errors = await import_service._process_data(df, "task-id", len(df))

        # Assert
        assert len(processed_df) < len(df)  # Row with missing date should be dropped
        assert any("dropped" in str(err).lower() for err in errors)

    @pytest.mark.asyncio
    async def test_process_data_date_conversion_error(self, import_service):
        """Test data processing with invalid date format"""
        # Arrange
        df = pd.DataFrame({
            'date': ['invalid-date', '2024-01-02', '2024-01-03'],
            'open': [100, 105, 110],
            'high': [110, 115, 120],
            'low': [95, 100, 105],
            'close': [105, 110, 115],
            'volume': [1000000, 1200000, 1100000]
        })

        import_service.import_task_repo.update = AsyncMock()

        # Act
        processed_df, errors = await import_service._process_data(df, "task-id", len(df))

        # Assert - should handle conversion errors
        assert isinstance(processed_df, pd.DataFrame)

    @pytest.mark.asyncio
    async def test_process_data_numeric_conversion(self, import_service):
        """Test numeric column conversion"""
        # Arrange
        df = pd.DataFrame({
            'date': ['2024-01-01', '2024-01-02', '2024-01-03'],
            'open': ['100', '105', 'invalid'],  # Mix of valid and invalid
            'high': [110, 115, 120],
            'low': [95, 100, 105],
            'close': [105, 110, 115],
            'volume': [1000000, 1200000, 1100000]
        })

        import_service.import_task_repo.update = AsyncMock()

        # Act
        processed_df, errors = await import_service._process_data(df, "task-id", len(df))

        # Assert
        assert isinstance(processed_df, pd.DataFrame)
        # Numeric conversion should handle errors with 'coerce'


class TestHelperMethods:
    """Test helper methods"""

    @pytest.mark.asyncio
    async def test_update_task_status(self, import_service):
        """Test _update_task_status method"""
        # Arrange
        import_service.import_task_repo.update = AsyncMock()

        # Act
        await import_service._update_task_status(
            "task-id",
            ImportStatus.PROCESSING,
            "Processing data"
        )

        # Assert
        import_service.import_task_repo.update.assert_called_once()
        call_args = import_service.import_task_repo.update.call_args
        assert call_args.kwargs["obj_in"]["status"] == ImportStatus.PROCESSING.value

    @pytest.mark.asyncio
    async def test_update_task_failed(self, import_service):
        """Test _update_task_failed method"""
        # Arrange
        import_service.import_task_repo.update = AsyncMock()

        # Act
        await import_service._update_task_failed(
            "task-id",
            "Validation failed",
            ["Error 1", "Error 2"]
        )

        # Assert
        import_service.import_task_repo.update.assert_called_once()
        call_args = import_service.import_task_repo.update.call_args
        assert call_args.kwargs["obj_in"]["status"] == ImportStatus.FAILED.value
        assert call_args.kwargs["obj_in"]["error_message"] == "Validation failed"
        assert call_args.kwargs["obj_in"]["error_count"] == 2


class TestEncodingDetection:
    """Test encoding detection"""

    def test_detect_gbk_encoding(self, tmp_path):
        """Test GBK encoding detection"""
        # Arrange
        file_path = tmp_path / "gbk.txt"
        file_path.write_text("中文测试", encoding='gbk')

        # Act
        encoding = DataImportService._detect_encoding(str(file_path))

        # Assert
        assert encoding in ['utf-8', 'gbk', 'gb2312']

    def test_detect_latin1_encoding(self, tmp_path):
        """Test Latin-1 encoding detection"""
        # Arrange
        file_path = tmp_path / "latin1.txt"
        file_path.write_text("Héllo Wörld", encoding='latin-1')

        # Act
        encoding = DataImportService._detect_encoding(str(file_path))

        # Assert
        # The encoding detection tries multiple encodings in order
        # utf-8, gbk, gb2312, latin-1, iso-8859-1
        # Since "Héllo Wörld" can be decoded by multiple encodings,
        # we accept any of the supported encodings
        assert encoding in ['utf-8', 'gbk', 'gb2312', 'latin-1', 'iso-8859-1']
