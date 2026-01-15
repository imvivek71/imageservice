<!--
Author: Vivek Kuumar Goswami
Date: January 15, 2026
-->

# S3 Image Structure & Resizing Strategy

## Overview

This document describes the S3 folder structure and image variant strategy for the Image Service API.

---

## S3 Folder Structure

```
s3://image-service-bucket/
└── images/
    └── user_id={user_id}/
        └── image_id={image_id}/
            ├── original.jpg       ← Full resolution (uploaded file)
            ├── medium.jpg         ← 1024x1024 max (feed/card view)
            └── thumbnail.jpg      ← 200x200 max (list/grid view)
```

### Example Path
```
s3://image-service-bucket/images/user_id=user123/image_id=550e8400-e29b-41d4-a716-446655440000/
├── original.jpg    (2560x1920, 2.5MB)
├── medium.jpg      (1024x768, 350KB)
└── thumbnail.jpg   (200x150, 45KB)
```

---

## Image Variants

### 1. Original
- **Max Size**: No resizing (original dimensions)
- **Use Case**: Downloads, high-quality viewing
- **Quality**: 85% JPEG quality
- **Storage**: Full resolution

### 2. Medium
- **Max Size**: 1024 x 1024 pixels
- **Aspect Ratio**: Maintained (fitted into 1024x1024)
- **Use Case**: Feed display, card views, detail pages
- **Quality**: 85% JPEG quality
- **Storage**: ~15-20% of original

### 3. Thumbnail
- **Max Size**: 200 x 200 pixels
- **Aspect Ratio**: Maintained (fitted into 200x200)
- **Use Case**: Grid/list views, previews
- **Quality**: 85% JPEG quality
- **Storage**: ~3-5% of original

---

## Image Processing

### Resizing Algorithm
- **Library**: Pillow (Python Imaging Library)
- **Method**: `Image.thumbnail()` with LANCZOS resampling
- **Aspect Ratio**: Always maintained
- **Format**: JPEG with 85% quality
- **Optimization**: Enabled

### Code Implementation (upload.py)

```python
def resize_image(image_data, max_size):
    """
    Resize image to specified dimensions while maintaining aspect ratio.
    """
    img = Image.open(BytesIO(image_data))
    if max_size:
        img.thumbnail(max_size, Image.Resampling.LANCZOS)
    output = BytesIO()
    img_format = img.format or 'JPEG'
    img.save(output, format=img_format, quality=85, optimize=True)
    output.seek(0)
    return output, img.size, img_format
```

### Upload Process

1. **Receive** image from client
2. **Parse** image metadata (user_id, tags, description)
3. **Generate** unique image_id and timestamp
4. **Create** S3 folder: `images/user_id={user_id}/image_id={image_id}/`
5. **Process** image variants:
   - **original.jpg**: Store as-is
   - **medium.jpg**: Resize to fit 1024x1024, save
   - **thumbnail.jpg**: Resize to fit 200x200, save
6. **Store** metadata in DynamoDB
7. **Return** response with image_id and variants

---

## DynamoDB Metadata

The metadata stored in DynamoDB tracks:

```json
{
  "image_id": "550e8400-e29b-41d4-a716-446655440000",
  "user_id": "user123",
  "s3_folder": "images/user_id=user123/image_id=550e8400-e29b-41d4-a716-446655440000",
  "s3_prefix": "images/user_id=user123/image_id=550e8400-e29b-41d4-a716-446655440000",
  "width": 2560,
  "height": 1920,
  "aspect_ratio": "4:3",
  "size_bytes": 2500000,
  "variants": ["original", "medium", "thumbnail"],
  "created_at": "2026-01-15T10:45:00Z",
  ...
}
```

---

## Presigned URLs

When retrieving an image (GET /images/{image_id}), the API returns presigned URLs for all variants:

```json
{
  "download_urls": {
    "original": "https://image-service-bucket.s3.amazonaws.com/images/user_id=user123/image_id=550e8400/original.jpg?X-Amz-Signature=...",
    "medium": "https://image-service-bucket.s3.amazonaws.com/images/user_id=user123/image_id=550e8400/medium.jpg?X-Amz-Signature=...",
    "thumbnail": "https://image-service-bucket.s3.amazonaws.com/images/user_id=user123/image_id=550e8400/thumbnail.jpg?X-Amz-Signature=..."
  },
  "default_url": "https://...medium.jpg?X-Amz-Signature=..."
}
```

### URL Expiration
- **Expiration Time**: 1 hour (3600 seconds)
- **Use Case**: Temporary secure access without authentication

---

## Storage Optimization

### Space Savings Example
Original 2.5MB image:
- **original.jpg**: 2.5 MB (100%)
- **medium.jpg**: 0.35 MB (14%)
- **thumbnail.jpg**: 0.045 MB (1.8%)
- **Total**: ~2.85 MB (114%)

For 10,000 images:
- **Without variants**: 25 GB
- **With variants**: 28.5 GB
- **Storage increase**: 14% (acceptable trade-off for performance)

### Benefits
✅ Faster page loads (smaller images)
✅ Reduced bandwidth
✅ Better UX for lists/grids
✅ CDN-friendly (cache-able)
✅ Mobile-optimized

---

## Deletion Process

When an image is deleted (DELETE /images/{image_id}):

1. **DynamoDB**: Mark as `is_deleted = True` (soft delete)
2. **S3**: Delete all variants:
   - `images/user_id={user_id}/image_id={image_id}/original.jpg`
   - `images/user_id={user_id}/image_id={image_id}/medium.jpg`
   - `images/user_id={user_id}/image_id={image_id}/thumbnail.jpg`
3. **Response**: Returns count of S3 objects deleted

---

## Environment Variables

Set these in the SAM template or Lambda environment:

```yaml
Environment:
  Variables:
    TABLE_NAME: ImageService
    BUCKET_NAME: image-service-bucket
```

---

## Supported Image Formats

Currently supported:
- JPEG (.jpg, .jpeg)
- PNG (.png)
- WebP (.webp)
- BMP (.bmp)

All are converted to JPEG for storage optimization.

---

## Future Enhancements

- [ ] Add WebP variant for better compression
- [ ] Implement progressive JPEG encoding
- [ ] Add image metadata extraction (EXIF)
- [ ] Implement image cropping/rotation
- [ ] Add image CDN integration (CloudFront)
- [ ] Implement image analysis (content moderation)
- [ ] Add batch image uploads
- [ ] Implement image versioning

---

## Performance Metrics

### Upload Time (Typical)
- 2.5 MB image
- Processing time: 2-5 seconds
- S3 upload time: 1-3 seconds
- DynamoDB write: 100-200 ms
- **Total**: ~3-8 seconds

### Retrieval Time
- Generate presigned URLs: 100-300 ms
- Query DynamoDB: 50-100 ms
- **Total**: ~150-400 ms

### Bandwidth Savings
- Thumbnail (200x200): ~45 KB → 180x reduction
- Medium (1024x1024): ~350 KB → 7x reduction
- Original: Full size

---

## Troubleshooting

### Image Upload Fails
- Check image file size (max 100 MB recommended)
- Verify image format is supported
- Check S3 bucket permissions
- Verify DynamoDB table exists

### Presigned URL Expired
- URL expires after 1 hour
- Request new URL from GET endpoint

### Image Not Found
- Verify image_id is correct
- Check if image was already deleted
- Query DynamoDB directly

---

For more details, see:
- [Pillow Documentation](https://pillow.readthedocs.io/)
- [AWS S3 Best Practices](https://docs.aws.amazon.com/s3/latest/userguide/)
- [Lambda Performance](https://docs.aws.amazon.com/lambda/latest/dg/best-practices.html)
