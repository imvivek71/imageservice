<!--
Author: Vivek Kuumar Goswami
Date: January 15, 2026
-->

# Image Processing Workflow

## Overview

The image service now uses an **asynchronous event-driven architecture** for image resizing:

1. **Upload API** → Uploads original image to S3
2. **S3 Event** → Triggered by PutObject on original.jpg
3. **Image Processor Lambda** → Creates resized variants
4. **DynamoDB Update** → Stores image dimensions and variant status

---

## Architecture Flow

```
┌─────────────────────────────────────────────────────────────┐
│ Client Upload Request                                       │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
        ┌────────────────────────────┐
        │  API Gateway /images POST  │
        └────────────┬───────────────┘
                     │
                     ▼
        ┌────────────────────────────┐
        │  Upload Lambda Function    │
        │  - Parse metadata          │
        │  - Upload original.jpg     │
        │  - Store in DynamoDB       │
        │  - Return 201 Created      │
        └────────────┬───────────────┘
                     │
                     ▼
        ┌────────────────────────────────────────┐
        │  S3 Bucket Event Notification          │
        │  (PutObject on images/user_id=*/      │
        │   image_id=*/original.jpg)             │
        └────────────┬─────────────────────────────┘
                     │
                     ▼
        ┌────────────────────────────────────────┐
        │  Image Processor Lambda (Async)        │
        │  - Download original.jpg               │
        │  - Resize to medium.jpg                │
        │  - Resize to thumbnail.jpg             │
        │  - Upload both to S3                   │
        │  - Extract image dimensions            │
        │  - Update DynamoDB                     │
        └────────────┬─────────────────────────────┘
                     │
                     ▼
        ┌────────────────────────────┐
        │  DynamoDB Updated          │
        │  - width, height set       │
        │  - variants: [original,    │
        │    medium, thumbnail]      │
        │  - processing_status: done │
        └────────────────────────────┘
```

---

## Detailed Flow

### Step 1: Upload API (upload.py)

**Endpoint**: `POST /images`

**Input**:
```json
{
  "queryStringParameters": {
    "user_id": "user123",
    "tags": "nature,landscape",
    "description": "Mountain view"
  },
  "body": "<binary image data>"
}
```

**Actions**:
1. Parse image data from request body
2. Generate unique `image_id` and `created_at` timestamp
3. Create S3 folder: `images/user_id=user123/image_id={uuid}/`
4. Upload to: `images/user_id=user123/image_id={uuid}/original.jpg`
5. Store metadata in DynamoDB with `processing_status: pending`
6. Return 201 with `variants: ['original']`

**DynamoDB Entry Created**:
```json
{
  "PK": "USER#user123",
  "SK": "IMAGE#2026-01-15T10:45:00Z#550e8400",
  "image_id": "550e8400",
  "s3_folder": "images/user_id=user123/image_id=550e8400",
  "variants": ["original"],
  "width": 0,
  "height": 0,
  "processing_status": "pending"
}
```

**Response** (201 Created):
```json
{
  "message": "Image uploaded successfully. Processing variants...",
  "image_id": "550e8400",
  "processing_status": "pending"
}
```

---

### Step 2: S3 Event Trigger

**Event**: `s3:ObjectCreated:*`

**Filter**:
- Prefix: `images/user_id=`
- Suffix: `original.jpg`

This ensures the Image Processor Lambda is only triggered when an original image is uploaded.

**S3 Event Payload**:
```json
{
  "Records": [
    {
      "s3": {
        "bucket": {
          "name": "image-service-bucket"
        },
        "object": {
          "key": "images/user_id=user123/image_id=550e8400/original.jpg"
        }
      }
    }
  ]
}
```

---

### Step 3: Image Processor Lambda (image_processor.py)

**Trigger**: S3 PutObject event

**Timeout**: 60 seconds
**Memory**: 1024 MB

**Actions**:
1. Extract user_id and image_id from S3 key
2. Download original.jpg from S3
3. Get original image dimensions
4. Create variants:
   - **medium.jpg**: Resize to fit 1024x1024
   - **thumbnail.jpg**: Resize to fit 200x200
5. Upload variants to S3 (same folder)
6. Query DynamoDB to find the image record
7. Update DynamoDB with:
   - `width` and `height` from original
   - `aspect_ratio` (e.g., "4:3")
   - `variants`: ["original", "medium", "thumbnail"]
   - `processing_status`: "completed"

**S3 Folder After Processing**:
```
images/user_id=user123/image_id=550e8400/
├── original.jpg    (uploaded by upload.py)
├── medium.jpg      (created by image_processor)
└── thumbnail.jpg   (created by image_processor)
```

**DynamoDB Entry Updated**:
```json
{
  "PK": "USER#user123",
  "SK": "IMAGE#2026-01-15T10:45:00Z#550e8400",
  "image_id": "550e8400",
  "width": 2560,
  "height": 1920,
  "aspect_ratio": "4:3",
  "variants": ["original", "medium", "thumbnail"],
  "processing_status": "completed"
}
```

---

## Timing

### Total Processing Time
- **Upload API**: 1-2 seconds
- **S3 Event delay**: 100-500 ms
- **Image Processor**: 2-5 seconds
- **Total**: ~3-7 seconds

### User Experience
- Client receives `201 Created` immediately (1-2 sec)
- Variants ready in background (2-5 sec more)
- Client can check status via `processing_status` field

---

## Error Handling

### Upload Fails
- S3 PutObject fails → API returns 500
- DynamoDB write fails → API returns 500

### Image Processor Fails
- Original.jpg missing → Logs error, continues
- Resizing fails → Logs error, continues with other variants
- DynamoDB update fails → Logs error, but variants still in S3

**Note**: Image Processor Lambda failures don't block the user. Check CloudWatch logs.

---

## Monitoring

### CloudWatch Logs

**Upload Lambda**:
- `Uploaded original image to images/user_id=xxx/image_id=yyy/original.jpg`

**Image Processor Lambda**:
- `Processing S3 object: s3://bucket/images/user_id=xxx/image_id=yyy/original.jpg`
- `Downloaded original image: 2500000 bytes`
- `Original image dimensions: 2560x1920`
- `Resized image from (2560, 1920) to (1024, 768)`
- `Uploaded medium variant to images/user_id=xxx/image_id=yyy/medium.jpg`
- `Updated DynamoDB with image dimensions and variants`

---

## Get Image (Updated Behavior)

**Endpoint**: `GET /images/{image_id}`

**Response**:
```json
{
  "image_id": "550e8400",
  "metadata": {
    "user_id": "user123",
    "width": 2560,
    "height": 1920,
    "aspect_ratio": "4:3",
    "variants": ["original", "medium", "thumbnail"],
    "processing_status": "completed"
  },
  "download_urls": {
    "original": "https://bucket.s3.amazonaws.com/images/user_id=user123/image_id=550e8400/original.jpg?X-Amz-Signature=...",
    "medium": "https://bucket.s3.amazonaws.com/images/user_id=user123/image_id=550e8400/medium.jpg?X-Amz-Signature=...",
    "thumbnail": "https://bucket.s3.amazonaws.com/images/user_id=user123/image_id=550e8400/thumbnail.jpg?X-Amz-Signature=..."
  },
  "default_url": "https://...medium.jpg?X-Amz-Signature=..."
}
```

---

## Benefits of Async Processing

✅ **Fast API Response**: Client gets 201 immediately
✅ **Decoupled**: Image processing independent from upload API
✅ **Scalable**: Multiple images processed in parallel
✅ **Resilient**: Processor failures don't block users
✅ **Observable**: Each Lambda logs independently
✅ **Cost-effective**: Pay only for processing time

---

## Deployment Notes

### SAM Template
The `template.yaml` now includes:
- S3 event source configuration on `ImageBucket`
- Event filter for `original.jpg` uploads
- `ImageProcessorFunction` with 1024 MB memory and 60-second timeout

### IAM Permissions
Auto-generated by SAM:
- `ImageProcessorFunction` → S3 GetObject, PutObject
- `ImageProcessorFunction` → DynamoDB Read/Write

---

## Testing

### Test Upload
```bash
curl -X POST http://127.0.0.1:3000/images \
  -H "Content-Type: application/json" \
  -d '{"user_id":"user123","tags":["nature"],"description":"Test"}'
```

Response will include `processing_status: "pending"`

### Test Get (Before Processing)
```bash
curl -X GET http://127.0.0.1:3000/images/550e8400
```

Will have `width: 0`, `height: 0`, `variants: ["original"]`

### Test Get (After Processing)
Wait 5 seconds, then:
```bash
curl -X GET http://127.0.0.1:3000/images/550e8400
```

Will have actual dimensions, all three variants

---

## Future Enhancements

- [ ] Add processing timeout handling
- [ ] Implement webhook notifications when processing completes
- [ ] Add support for more image formats (WebP, AVIF)
- [ ] Implement image optimization per device (mobile, tablet, desktop)
- [ ] Add progress tracking for large images
- [ ] Implement image cropping/rotation
- [ ] Add Rekognition for content moderation

---

For more details, see:
- [S3_STRUCTURE.MD](S3_STRUCTURE.MD)
- [LOCALSTACK_GUIDE.MD](LOCALSTACK_GUIDE.MD)
- [template.yaml](template.yaml)
