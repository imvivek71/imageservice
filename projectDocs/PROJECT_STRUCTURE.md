# Project Structure - Image Service

Production-ready folder organization with separation of concerns.

```
src/
├── handlers/                    # Lambda function entry points
│   ├── __init__.py
│   ├── upload.py               # POST /images
│   ├── list.py                 # GET /images
│   ├── get.py                  # GET /images/{imageId}
│   ├── delete.py               # DELETE /images/{imageId}
│   └── image_processor.py       # S3 event processor for image variants
│
├── services/                    # Business logic & data access layers
│   ├── __init__.py
│   ├── dynamodb_service.py     # DynamoDB operations (CRUD)
│   ├── s3_service.py           # S3 operations (upload, download, presigned URLs)
│   └── image_service.py        # Image business logic (uses DynamoDB + S3)
│
├── utils/                       # Shared utilities
│   ├── __init__.py
│   ├── logger.py               # Centralized logging setup
│   └── response.py             # Standardized API responses (JSON encoding, error handling)
│
└── __init__.py
```

## Layer Explanation

### Handlers (`src/handlers/`)
- **Purpose**: Lambda function entry points
- **Responsibility**: Extract request data, validate input, call services, return responses
- **Keep them slim**: No business logic, just orchestration
- **Examples**:
  - `upload.py`: Validates user_id, calls S3Service and DynamoDBService
  - `list.py`: Calls ImageService.get_images_by_user()
  - `get.py`: Finds image, generates presigned URLs
  - `delete.py`: Soft deletes in DynamoDB, hard deletes from S3

### Services (`src/services/`)

#### 1. **dynamodb_service.py** - Low-level database operations
```
DynamoDBService
├── put_item()              # Insert/update item
├── get_item()              # Retrieve by PK+SK
├── query_by_pk()           # Query by partition key
├── scan()                  # Scan with filters
├── update_item()           # Update specific fields
├── delete_item()           # Delete by PK+SK
└── scan_by_attribute()     # Search by attribute (e.g., image_id)
```

#### 2. **s3_service.py** - Low-level S3 operations
```
S3Service
├── upload_object()         # Upload binary data
├── download_object()       # Download binary data
├── delete_object()         # Delete object
├── generate_presigned_url()# Get temporary download link
└── list_objects()          # List objects with prefix
```

#### 3. **image_service.py** - High-level business logic
```
ImageService
├── find_by_image_id()           # Find image (uses DynamoDB)
├── get_images_by_user()         # Get user's images with filtering
├── generate_download_urls()     # Generate variant URLs (uses S3Service)
├── delete_image_variants()      # Delete all S3 variants
└── soft_delete_image()          # Mark as deleted in DynamoDB
```

**Key principle**: Use DynamoDBService + S3Service to implement business logic

### Utils (`src/utils/`)

#### 1. **logger.py** - Centralized logging
```python
from utils.logger import get_logger

logger = get_logger(__name__)
logger.info("User ID: user123")
logger.error("Failed to upload", exc_info=True)
```

#### 2. **response.py** - Standardized responses
```python
from utils.response import error_response, success_response

# Automatic Decimal → int/float conversion
return success_response(200, {'items': dynamodb_items})
return error_response(404, 'Image not found')
```

## Benefits of This Structure

✅ **Separation of Concerns**
- Handlers: Request/Response
- Services: Business Logic & Data Access
- Utils: Shared tools

✅ **Easy to Test**
- Mock services in handlers
- Test services independently

✅ **Scalable**
- Add new handlers without changing services
- Modify service logic without touching handlers
- Reuse services across multiple handlers

✅ **Maintainable**
- Each module has single responsibility
- Clear dependencies
- Easy to find code

✅ **Production-Ready**
- Proper logging throughout
- Error handling at each layer
- Standardized responses

## How Requests Flow

```
POST /images
    ↓
handlers/upload.py
    ↓
services/s3_service.upload_object()  (uploads to S3)
    ↓
services/dynamodb_service.put_item()  (stores metadata)
    ↓
utils/response.success_response()  (returns JSON)
```

## Adding New Features

### Example: Add a "Like" endpoint

1. **Create handler** (`handlers/like.py`):
```python
def lambda_handler(event, context):
    image_id = event['pathParameters']['imageId']
    image = ImageService.find_by_image_id(image_id)
    # Update likes_count using DynamoDBService
```

2. **Add method to ImageService** (`services/image_service.py`):
```python
@staticmethod
def like_image(pk, sk):
    return DynamoDBService.update_item(...)
```

3. **Update template.yaml** - add new function with handler: `handlers.like.lambda_handler`

## Dependencies

- **AWS SDK**: `boto3` (already configured in handlers)
- **Image Processing**: `Pillow` (used in image_processor.py)
- **Logging**: Built-in `logging` module

## Environment Variables

Set in `template.yaml`:
- `TABLE_NAME`: DynamoDB table name
- `BUCKET_NAME`: S3 bucket name

All services read these automatically.
