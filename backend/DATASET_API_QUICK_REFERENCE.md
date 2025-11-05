# Dataset API Quick Reference

## Base URL
```
http://localhost:8000/api/datasets
```

---

## Endpoints

### 1. List Datasets
```http
GET /api/datasets
```

**Query Parameters**:
- `skip` (int, optional): Number of records to skip (default: 0)
- `limit` (int, optional): Max records to return (default: 100, max: 1000)
- `source` (str, optional): Filter by source (local, qlib, thirdparty)
- `status` (str, optional): Filter by status (valid, invalid, pending)
- `search` (str, optional): Search by name (case-insensitive)

**Example**:
```bash
curl "http://localhost:8000/api/datasets?skip=0&limit=10&source=local&status=valid&search=stock"
```

**Response** (200):
```json
{
  "total": 100,
  "items": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "name": "Stock Data 2024",
      "source": "local",
      "file_path": "/data/stocks_2024.csv",
      "status": "valid",
      "row_count": 10000,
      "columns": ["date", "symbol", "open", "high", "low", "close"],
      "metadata": {"description": "Daily stock data"},
      "created_at": "2024-01-01T00:00:00Z",
      "updated_at": "2024-01-01T00:00:00Z"
    }
  ]
}
```

---

### 2. Get Dataset by ID
```http
GET /api/datasets/{dataset_id}
```

**Example**:
```bash
curl "http://localhost:8000/api/datasets/550e8400-e29b-41d4-a716-446655440000"
```

**Response** (200):
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "Stock Data 2024",
  "source": "local",
  "file_path": "/data/stocks_2024.csv",
  "status": "valid",
  "row_count": 10000,
  "columns": ["date", "symbol", "open", "high", "low", "close"],
  "metadata": {"description": "Daily stock data"},
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z"
}
```

**Errors**:
- 404: Dataset not found

---

### 3. Create Dataset
```http
POST /api/datasets
Content-Type: application/json
```

**Request Body**:
```json
{
  "name": "Stock Data 2024",
  "source": "local",
  "file_path": "/data/stocks_2024.csv",
  "extra_metadata": {
    "description": "Daily stock data",
    "format": "csv",
    "date_range": "2024-01-01 to 2024-12-31"
  }
}
```

**Fields**:
- `name` (str, required): Dataset name (1-255 chars)
- `source` (enum, required): "local", "qlib", or "thirdparty"
- `file_path` (str, required): File path or URI
- `extra_metadata` (object, optional): Additional metadata (default: {})

**Example**:
```bash
curl -X POST "http://localhost:8000/api/datasets" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Stock Data 2024",
    "source": "local",
    "file_path": "/data/stocks_2024.csv",
    "extra_metadata": {"description": "Daily stock data"}
  }'
```

**Response** (201):
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "Stock Data 2024",
  "source": "local",
  "file_path": "/data/stocks_2024.csv",
  "status": "pending",
  "row_count": 0,
  "columns": [],
  "metadata": {"description": "Daily stock data"},
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z"
}
```

**Errors**:
- 400: Validation error (invalid data)
- 409: Dataset name already exists
- 422: Pydantic validation error

---

### 4. Update Dataset
```http
PUT /api/datasets/{dataset_id}
Content-Type: application/json
```

**Request Body** (all fields optional):
```json
{
  "name": "Updated Name",
  "status": "valid",
  "row_count": 10000,
  "columns": ["date", "symbol", "open", "high", "low", "close"],
  "extra_metadata": {"description": "Updated description"}
}
```

**Fields**:
- `name` (str, optional): New dataset name
- `status` (enum, optional): "valid", "invalid", or "pending"
- `row_count` (int, optional): Number of rows (>= 0)
- `columns` (array, optional): List of column names
- `extra_metadata` (object, optional): Additional metadata

**Example** (Full Update):
```bash
curl -X PUT "http://localhost:8000/api/datasets/550e8400-e29b-41d4-a716-446655440000" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Stock Data 2024 Updated",
    "status": "valid",
    "row_count": 10000,
    "columns": ["date", "symbol", "price"],
    "extra_metadata": {"updated": true}
  }'
```

**Example** (Partial Update):
```bash
curl -X PUT "http://localhost:8000/api/datasets/550e8400-e29b-41d4-a716-446655440000" \
  -H "Content-Type: application/json" \
  -d '{"status": "valid"}'
```

**Response** (200):
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "Stock Data 2024 Updated",
  "source": "local",
  "file_path": "/data/stocks_2024.csv",
  "status": "valid",
  "row_count": 10000,
  "columns": ["date", "symbol", "price"],
  "metadata": {"updated": true},
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T12:00:00Z"
}
```

**Errors**:
- 400: Validation error
- 404: Dataset not found
- 409: Dataset name conflict

---

### 5. Delete Dataset
```http
DELETE /api/datasets/{dataset_id}
```

**Query Parameters**:
- `hard_delete` (bool, optional): If true, permanently delete; if false, soft delete (default: false)

**Example** (Soft Delete):
```bash
curl -X DELETE "http://localhost:8000/api/datasets/550e8400-e29b-41d4-a716-446655440000"
```

**Example** (Hard Delete):
```bash
curl -X DELETE "http://localhost:8000/api/datasets/550e8400-e29b-41d4-a716-446655440000?hard_delete=true"
```

**Response** (204): No Content

**Errors**:
- 404: Dataset not found
- 500: Database error

---

## HTTP Status Codes

| Code | Meaning | Usage |
|------|---------|-------|
| 200 | OK | Successful GET/PUT |
| 201 | Created | Successful POST |
| 204 | No Content | Successful DELETE |
| 400 | Bad Request | Validation error |
| 404 | Not Found | Resource doesn't exist |
| 409 | Conflict | Duplicate name/constraint violation |
| 422 | Unprocessable Entity | Pydantic validation error |
| 500 | Internal Server Error | Database/unexpected error |

---

## Error Response Format

```json
{
  "detail": "Dataset with name 'Stock Data' already exists"
}
```

---

## Special Headers

### Correlation ID (Request Tracking)

Include this header for distributed tracing:

```bash
curl -H "X-Correlation-ID: req-12345" "http://localhost:8000/api/datasets"
```

If not provided, a UUID will be auto-generated.

---

## Python Client Example

```python
import httpx
import asyncio

async def main():
    async with httpx.AsyncClient(base_url="http://localhost:8000") as client:
        # Create dataset
        response = await client.post(
            "/api/datasets",
            json={
                "name": "My Dataset",
                "source": "local",
                "file_path": "/data/my_data.csv",
                "extra_metadata": {"description": "Test dataset"}
            }
        )
        dataset = response.json()
        print(f"Created: {dataset['id']}")

        # List datasets
        response = await client.get(
            "/api/datasets",
            params={"source": "local", "limit": 10}
        )
        datasets = response.json()
        print(f"Found {datasets['total']} datasets")

        # Update dataset
        response = await client.put(
            f"/api/datasets/{dataset['id']}",
            json={"status": "valid", "row_count": 1000}
        )
        updated = response.json()
        print(f"Updated: {updated['status']}")

        # Delete dataset
        response = await client.delete(f"/api/datasets/{dataset['id']}")
        print(f"Deleted: {response.status_code == 204}")

asyncio.run(main())
```

---

## JavaScript/TypeScript Client Example

```typescript
const BASE_URL = "http://localhost:8000/api/datasets";

// Create dataset
const createDataset = async () => {
  const response = await fetch(BASE_URL, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      name: "My Dataset",
      source: "local",
      file_path: "/data/my_data.csv",
      extra_metadata: { description: "Test dataset" }
    })
  });
  return await response.json();
};

// List datasets
const listDatasets = async (params = {}) => {
  const query = new URLSearchParams(params).toString();
  const response = await fetch(`${BASE_URL}?${query}`);
  return await response.json();
};

// Get dataset
const getDataset = async (id) => {
  const response = await fetch(`${BASE_URL}/${id}`);
  return await response.json();
};

// Update dataset
const updateDataset = async (id, updates) => {
  const response = await fetch(`${BASE_URL}/${id}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(updates)
  });
  return await response.json();
};

// Delete dataset
const deleteDataset = async (id, hardDelete = false) => {
  const url = hardDelete ? `${BASE_URL}/${id}?hard_delete=true` : `${BASE_URL}/${id}`;
  await fetch(url, { method: "DELETE" });
};

// Usage
const dataset = await createDataset();
const datasets = await listDatasets({ source: "local", limit: 10 });
await updateDataset(dataset.id, { status: "valid" });
await deleteDataset(dataset.id);
```

---

## Common Workflows

### 1. Import and Validate Dataset

```bash
# 1. Create dataset (status: pending)
DATASET_ID=$(curl -X POST "http://localhost:8000/api/datasets" \
  -H "Content-Type: application/json" \
  -d '{"name": "New Dataset", "source": "local", "file_path": "/data/file.csv"}' \
  | jq -r '.id')

# 2. Process/validate dataset (your logic)
# ...

# 3. Update status to valid
curl -X PUT "http://localhost:8000/api/datasets/$DATASET_ID" \
  -H "Content-Type: application/json" \
  -d '{"status": "valid", "row_count": 10000, "columns": ["col1", "col2"]}'
```

### 2. Search and Filter

```bash
# Find all valid local datasets with "stock" in name
curl "http://localhost:8000/api/datasets?source=local&status=valid&search=stock"
```

### 3. Batch Update

```bash
# Get all pending datasets
DATASETS=$(curl "http://localhost:8000/api/datasets?status=pending" | jq -r '.items[].id')

# Update each to valid
for ID in $DATASETS; do
  curl -X PUT "http://localhost:8000/api/datasets/$ID" \
    -H "Content-Type: application/json" \
    -d '{"status": "valid"}'
done
```

---

## Interactive API Documentation

Once the server is running, visit:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

These provide interactive API exploration and testing.

---

## Tips & Best Practices

1. **Always use correlation IDs** for request tracking in production
2. **Use soft delete** by default to allow recovery
3. **Validate data** before setting status to "valid"
4. **Use pagination** for large datasets (avoid loading all at once)
5. **Use search/filters** to reduce response size
6. **Handle errors** gracefully with proper status code checking
7. **Set metadata** early for better dataset discovery
8. **Use transactions** when making multiple related updates

---

## Troubleshooting

### Dataset not found (404)
- Check the dataset ID is correct
- Verify dataset wasn't soft-deleted
- Check database connectivity

### Duplicate name (409)
- Dataset names must be unique
- Check if a dataset with this name exists
- Soft-deleted datasets also count

### Validation errors (400/422)
- Check request body format
- Verify all required fields are provided
- Check field types and constraints
- Review error message for specific issues

### Database errors (500)
- Check database connection
- Verify database schema is up to date
- Check server logs for details
- Ensure database user has proper permissions

---

## Support

For issues or questions:
1. Check server logs: `/backend/logs/qlib-ui_*.log`
2. Review migration summary: `/backend/MIGRATION_SUMMARY.md`
3. Run tests: `pytest tests/test_dataset_api_migration.py -v`
4. Check database: Verify tables exist and data is correct
