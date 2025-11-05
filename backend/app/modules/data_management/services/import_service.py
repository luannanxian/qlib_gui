"""
Data Import Service

Handles file upload, validation, parsing, and dataset creation for CSV/Excel files.
Manages ImportTask lifecycle and progress tracking.
"""

import os
import io
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List, Tuple
from pathlib import Path

import pandas as pd
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.repositories.import_task import ImportTaskRepository
from app.database.repositories.dataset import DatasetRepository
from app.database.models.import_task import ImportStatus, ImportType
from app.database.models.dataset import DatasetStatus, DataSource
from app.modules.data_management.schemas.import_schemas import (
    ImportTaskCreate,
    ImportTaskUpdate,
    FileValidationResult,
    DataProcessingResult,
)


class DataImportService:
    """
    Service for handling data import operations.

    Provides methods for:
    - File validation and encoding detection
    - Data parsing and processing
    - ImportTask management
    - Dataset creation from imported data
    """

    # Required columns for stock data
    REQUIRED_COLUMNS = {"date", "open", "high", "low", "close", "volume"}

    # Supported file extensions
    SUPPORTED_EXTENSIONS = {".csv", ".xlsx", ".xls"}

    # Maximum file size (100MB default)
    MAX_FILE_SIZE = 100 * 1024 * 1024

    def __init__(
        self,
        session: AsyncSession,
        upload_dir: str = "./data/uploads"
    ):
        """
        Initialize DataImportService.

        Args:
            session: Async database session
            upload_dir: Directory for uploaded files
        """
        self.session = session
        self.import_task_repo = ImportTaskRepository(session)
        self.dataset_repo = DatasetRepository(session)
        self.upload_dir = Path(upload_dir)
        self.upload_dir.mkdir(parents=True, exist_ok=True)

    async def create_import_task(
        self,
        task_data: ImportTaskCreate
    ) -> str:
        """
        Create a new import task.

        Args:
            task_data: Import task creation data

        Returns:
            Import task ID
        """
        task = await self.import_task_repo.create(
            obj_in=task_data.model_dump(),
            commit=True
        )

        logger.info(
            f"Created import task {task.id}",
            task_id=task.id,
            filename=task_data.original_filename
        )

        return task.id

    async def validate_file(
        self,
        file_path: str,
        import_type: ImportType
    ) -> FileValidationResult:
        """
        Validate uploaded file format, encoding, and structure.

        Args:
            file_path: Path to uploaded file
            import_type: Type of import (csv, excel)

        Returns:
            FileValidationResult with validation status
        """
        errors = []
        warnings = []
        metadata = {}

        # Check file exists
        if not os.path.exists(file_path):
            errors.append(f"File not found: {file_path}")
            return FileValidationResult(
                is_valid=False,
                errors=errors,
                warnings=warnings,
                metadata=metadata
            )

        # Check file size
        file_size = os.path.getsize(file_path)
        if file_size > self.MAX_FILE_SIZE:
            errors.append(
                f"File size {file_size} bytes exceeds maximum "
                f"{self.MAX_FILE_SIZE} bytes"
            )

        # Check file extension
        file_ext = Path(file_path).suffix.lower()
        if file_ext not in self.SUPPORTED_EXTENSIONS:
            errors.append(
                f"Unsupported file extension: {file_ext}. "
                f"Supported: {', '.join(self.SUPPORTED_EXTENSIONS)}"
            )

        if errors:
            return FileValidationResult(
                is_valid=False,
                errors=errors,
                warnings=warnings,
                metadata=metadata
            )

        # Try to read file and detect encoding
        try:
            if import_type == ImportType.CSV:
                # Detect encoding for CSV
                encoding = self._detect_encoding(file_path)
                metadata["encoding"] = encoding

                # Read first few rows to validate structure
                df_sample = pd.read_csv(
                    file_path,
                    encoding=encoding,
                    nrows=5
                )

                # Detect delimiter
                with open(file_path, 'r', encoding=encoding) as f:
                    first_line = f.readline()
                    if ',' in first_line:
                        metadata["delimiter"] = ","
                    elif '\t' in first_line:
                        metadata["delimiter"] = "\t"
                    elif ';' in first_line:
                        metadata["delimiter"] = ";"
                    else:
                        metadata["delimiter"] = ","

            elif import_type in [ImportType.EXCEL]:
                # Read Excel file
                df_sample = pd.read_excel(file_path, nrows=5)
                metadata["encoding"] = "utf-8"  # Excel is binary
                metadata["delimiter"] = None

            else:
                errors.append(f"Unsupported import type: {import_type}")
                return FileValidationResult(
                    is_valid=False,
                    errors=errors,
                    warnings=warnings,
                    metadata=metadata
                )

            # Validate columns
            columns = set(col.lower().strip() for col in df_sample.columns)
            metadata["columns"] = list(df_sample.columns)
            metadata["total_rows"] = len(df_sample)

            # Check for required columns
            missing_cols = self.REQUIRED_COLUMNS - columns
            if missing_cols:
                errors.append(
                    f"Missing required columns: {', '.join(missing_cols)}. "
                    f"Required: {', '.join(self.REQUIRED_COLUMNS)}"
                )

            # Check for empty dataframe
            if df_sample.empty:
                warnings.append("File appears to be empty or contains only headers")

            # Check for missing values
            missing_counts = df_sample.isnull().sum()
            for col, count in missing_counts.items():
                if count > 0:
                    warnings.append(
                        f"Column '{col}' has {count} missing values "
                        f"in first 5 rows"
                    )

        except Exception as e:
            logger.error(f"Error validating file {file_path}: {e}")
            errors.append(f"File validation error: {str(e)}")

        is_valid = len(errors) == 0

        return FileValidationResult(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
            metadata=metadata
        )

    async def process_import(
        self,
        task_id: str,
        file_path: str,
        import_type: ImportType,
        import_config: Optional[Dict[str, Any]] = None
    ) -> DataProcessingResult:
        """
        Process imported data file and create dataset.

        Args:
            task_id: Import task ID
            file_path: Path to file
            import_type: Type of import
            import_config: Import configuration

        Returns:
            DataProcessingResult with processing outcome
        """
        import_config = import_config or {}
        errors = []
        rows_skipped = 0

        try:
            # Update task status to VALIDATING
            await self._update_task_status(
                task_id,
                ImportStatus.VALIDATING,
                "Validating file format"
            )

            # Validate file
            validation = await self.validate_file(file_path, import_type)

            if not validation.is_valid:
                await self._update_task_failed(
                    task_id,
                    "File validation failed",
                    validation.errors
                )
                return DataProcessingResult(
                    success=False,
                    rows_processed=0,
                    rows_skipped=0,
                    errors=[{"message": err} for err in validation.errors]
                )

            # Update task with validation metadata
            await self.import_task_repo.update(
                id=task_id,
                obj_in={
                    "parsing_metadata": validation.metadata,
                    "status": ImportStatus.PARSING.value
                },
                commit=True
            )

            # Parse file
            df = await self._parse_file(
                file_path,
                import_type,
                validation.metadata,
                import_config
            )

            total_rows = len(df)

            # Update task with total rows
            await self.import_task_repo.update(
                id=task_id,
                obj_in={
                    "total_rows": total_rows,
                    "status": ImportStatus.PROCESSING.value
                },
                commit=True
            )

            # Process data
            df_processed, processing_errors = await self._process_data(
                df,
                task_id,
                total_rows
            )

            if processing_errors:
                errors.extend(processing_errors)

            rows_processed = len(df_processed)
            rows_skipped = total_rows - rows_processed

            # Create dataset from processed data
            dataset_id = await self._create_dataset(
                task_id,
                df_processed,
                file_path,
                validation.metadata
            )

            # Update task to completed
            await self.import_task_repo.update(
                id=task_id,
                obj_in={
                    "status": ImportStatus.COMPLETED.value,
                    "processed_rows": rows_processed,
                    "progress_percentage": 100.0,
                    "dataset_id": dataset_id,
                    "error_count": len(errors)
                },
                commit=True
            )

            logger.info(
                f"Import task {task_id} completed successfully",
                task_id=task_id,
                dataset_id=dataset_id,
                rows_processed=rows_processed,
                rows_skipped=rows_skipped
            )

            return DataProcessingResult(
                success=True,
                rows_processed=rows_processed,
                rows_skipped=rows_skipped,
                errors=[{"message": str(e)} for e in errors],
                dataset_id=dataset_id,
                dataset_metadata={
                    "columns": list(df_processed.columns),
                    "row_count": rows_processed,
                    "data_types": {col: str(dtype) for col, dtype in df_processed.dtypes.items()}
                }
            )

        except Exception as e:
            logger.error(
                f"Error processing import task {task_id}: {e}",
                exc_info=True
            )
            await self._update_task_failed(
                task_id,
                f"Processing error: {str(e)}",
                []
            )
            return DataProcessingResult(
                success=False,
                rows_processed=0,
                rows_skipped=0,
                errors=[{"message": f"Processing error: {str(e)}"}]
            )

    async def _parse_file(
        self,
        file_path: str,
        import_type: ImportType,
        metadata: Dict[str, Any],
        config: Dict[str, Any]
    ) -> pd.DataFrame:
        """Parse file into pandas DataFrame."""
        if import_type == ImportType.CSV:
            encoding = metadata.get("encoding", "utf-8")
            delimiter = metadata.get("delimiter", ",")

            df = pd.read_csv(
                file_path,
                encoding=encoding,
                delimiter=delimiter,
                skipinitialspace=True,
                **config
            )

        elif import_type in [ImportType.EXCEL]:
            df = pd.read_excel(file_path, **config)

        else:
            raise ValueError(f"Unsupported import type: {import_type}")

        # Normalize column names (lowercase, strip whitespace)
        df.columns = [col.lower().strip() for col in df.columns]

        return df

    async def _process_data(
        self,
        df: pd.DataFrame,
        task_id: str,
        total_rows: int
    ) -> Tuple[pd.DataFrame, List[str]]:
        """
        Process and clean data.

        Returns:
            Tuple of (processed_dataframe, list_of_errors)
        """
        errors = []

        # Convert date column to datetime
        if 'date' in df.columns:
            try:
                df['date'] = pd.to_datetime(df['date'])
            except Exception as e:
                errors.append(f"Error converting date column: {e}")

        # Convert numeric columns
        numeric_cols = ['open', 'high', 'low', 'close', 'volume']
        for col in numeric_cols:
            if col in df.columns:
                try:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
                except Exception as e:
                    errors.append(f"Error converting {col} to numeric: {e}")

        # Remove rows with missing critical data
        initial_count = len(df)
        df = df.dropna(subset=['date', 'close'])
        rows_dropped = initial_count - len(df)

        if rows_dropped > 0:
            errors.append(
                f"Dropped {rows_dropped} rows with missing date or close price"
            )

        # Handle missing values in other columns (forward fill)
        df = df.fillna(method='ffill')
        df = df.fillna(method='bfill')

        # Update progress
        progress = min(80.0, (len(df) / total_rows) * 100)
        await self.import_task_repo.update(
            id=task_id,
            obj_in={
                "processed_rows": len(df),
                "progress_percentage": progress
            },
            commit=True
        )

        return df, errors

    async def _create_dataset(
        self,
        task_id: str,
        df: pd.DataFrame,
        file_path: str,
        metadata: Dict[str, Any]
    ) -> str:
        """Create dataset from processed data."""
        task = await self.import_task_repo.get(task_id)

        dataset_data = {
            "name": task.task_name,
            "source": DataSource.LOCAL.value,
            "file_path": file_path,
            "status": DatasetStatus.VALID.value,
            "row_count": len(df),
            "columns": list(df.columns),
            "extra_metadata": {
                "import_task_id": task_id,
                "original_filename": task.original_filename,
                "encoding": metadata.get("encoding"),
                "delimiter": metadata.get("delimiter"),
                "data_types": {col: str(dtype) for col, dtype in df.dtypes.items()}
            }
        }

        dataset = await self.dataset_repo.create(
            obj_in=dataset_data,
            commit=True
        )

        return dataset.id

    async def _update_task_status(
        self,
        task_id: str,
        status: ImportStatus,
        message: Optional[str] = None
    ) -> None:
        """Update task status."""
        await self.import_task_repo.update(
            id=task_id,
            obj_in={"status": status.value},
            commit=True
        )

        if message:
            logger.info(f"Task {task_id}: {message}", task_id=task_id)

    async def _update_task_failed(
        self,
        task_id: str,
        error_message: str,
        validation_errors: List[str]
    ) -> None:
        """Update task as failed."""
        await self.import_task_repo.update(
            id=task_id,
            obj_in={
                "status": ImportStatus.FAILED.value,
                "error_message": error_message,
                "validation_errors": [{"error": err} for err in validation_errors],
                "error_count": len(validation_errors)
            },
            commit=True
        )

        logger.error(
            f"Task {task_id} failed: {error_message}",
            task_id=task_id,
            errors=validation_errors
        )

    @staticmethod
    def _detect_encoding(file_path: str, sample_size: int = 10000) -> str:
        """
        Detect file encoding by trying common encodings.

        Args:
            file_path: Path to file
            sample_size: Number of bytes to sample

        Returns:
            Detected encoding name
        """
        encodings = ['utf-8', 'gbk', 'gb2312', 'latin-1', 'iso-8859-1']

        for encoding in encodings:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    f.read(sample_size)
                return encoding
            except (UnicodeDecodeError, LookupError):
                continue

        # Default to utf-8 if nothing works
        return 'utf-8'
