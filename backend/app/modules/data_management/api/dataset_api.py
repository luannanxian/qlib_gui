"""Dataset API Endpoints"""

from typing import List
from fastapi import APIRouter, HTTPException, status
from app.modules.data_management.schemas.dataset import (
    DatasetCreate,
    DatasetUpdate,
    DatasetResponse,
    DatasetListResponse
)
from app.modules.data_management.models.dataset import Dataset, DatasetStatus

router = APIRouter(prefix="/api/datasets", tags=["datasets"])

# In-memory storage for now (will be replaced with database later)
_datasets: dict[str, Dataset] = {}


@router.get("", response_model=DatasetListResponse)
async def list_datasets():
    """List all datasets."""
    datasets = list(_datasets.values())
    return DatasetListResponse(
        total=len(datasets),
        items=[
            DatasetResponse(
                id=ds.id,
                name=ds.name,
                source=ds.source,
                file_path=ds.file_path,
                status=ds.status,
                row_count=ds.row_count,
                columns=ds.columns,
                metadata=ds.metadata,
                created_at=ds.created_at,
                updated_at=ds.updated_at
            )
            for ds in datasets
        ]
    )


@router.get("/{dataset_id}", response_model=DatasetResponse)
async def get_dataset(dataset_id: str):
    """Get a dataset by ID."""
    if dataset_id not in _datasets:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dataset with id {dataset_id} not found"
        )

    ds = _datasets[dataset_id]
    return DatasetResponse(
        id=ds.id,
        name=ds.name,
        source=ds.source,
        file_path=ds.file_path,
        status=ds.status,
        row_count=ds.row_count,
        columns=ds.columns,
        metadata=ds.metadata,
        created_at=ds.created_at,
        updated_at=ds.updated_at
    )


@router.post("", response_model=DatasetResponse, status_code=status.HTTP_201_CREATED)
async def create_dataset(dataset_in: DatasetCreate):
    """Create a new dataset."""
    dataset = Dataset(
        name=dataset_in.name,
        source=dataset_in.source,
        file_path=dataset_in.file_path,
        status=DatasetStatus.PENDING
    )

    _datasets[dataset.id] = dataset

    return DatasetResponse(
        id=dataset.id,
        name=dataset.name,
        source=dataset.source,
        file_path=dataset.file_path,
        status=dataset.status,
        row_count=dataset.row_count,
        columns=dataset.columns,
        metadata=dataset.metadata,
        created_at=dataset.created_at,
        updated_at=dataset.updated_at
    )


@router.put("/{dataset_id}", response_model=DatasetResponse)
async def update_dataset(dataset_id: str, dataset_in: DatasetUpdate):
    """Update a dataset."""
    if dataset_id not in _datasets:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dataset with id {dataset_id} not found"
        )

    dataset = _datasets[dataset_id]

    # Update fields if provided
    if dataset_in.name is not None:
        dataset.name = dataset_in.name
    if dataset_in.status is not None:
        dataset.status = dataset_in.status
    if dataset_in.row_count is not None:
        dataset.row_count = dataset_in.row_count
    if dataset_in.columns is not None:
        dataset.columns = dataset_in.columns
    if dataset_in.metadata is not None:
        dataset.metadata = dataset_in.metadata

    # Update timestamp
    from datetime import datetime
    dataset.updated_at = datetime.utcnow()

    return DatasetResponse(
        id=dataset.id,
        name=dataset.name,
        source=dataset.source,
        file_path=dataset.file_path,
        status=dataset.status,
        row_count=dataset.row_count,
        columns=dataset.columns,
        metadata=dataset.metadata,
        created_at=dataset.created_at,
        updated_at=dataset.updated_at
    )


@router.delete("/{dataset_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_dataset(dataset_id: str):
    """Delete a dataset."""
    if dataset_id not in _datasets:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dataset with id {dataset_id} not found"
        )

    del _datasets[dataset_id]
