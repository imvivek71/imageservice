<!--
Author: Vivek Kuumar Goswami
Date: January 15, 2026
-->

# Image Upload & Metadata Service – DynamoDB Design

This document describes the **DynamoDB single-table schema** for an Instagram-like
image upload and storage service.

The system uses:
- API Gateway
- AWS Lambda (Python 3.7+)
- Amazon S3 (image binaries)
- Amazon DynamoDB (image metadata)

The schema is **access-pattern driven**, optimized for:
- High concurrency
- Latest → oldest listing
- Low latency API calls
- Horizontal scalability

---

## High-Level Architecture

- **Images** are stored in **Amazon S3**
- **Image metadata** is stored in **Amazon DynamoDB**
- APIs interact only with metadata
- Image access uses **S3 pre-signed URLs**

---

## What Is Image Metadata?

**Image metadata** is all non-binary information required to identify, store,
display, filter, secure, and manage an image.

### Metadata Includes
- Ownership
- Storage location
- Upload time
- Visibility
- Tags
- Image properties
- Engagement counters

### Metadata Does NOT Include
- Image binary
- Base64 image data
- Large EXIF blobs

---

## DynamoDB Table Overview

**Table Name:** `ImageService`

**Table Type:** Single-table design

---

## Primary Key Design

### Partition Key (PK)

PK = USER#<user_id>

- Groups all images belonging to a user
- Enables fast per-user listing
- Prevents hot partitions

### Sort Key (SK)

SK = IMAGE#<created_at>#<image_id>

- Orders images by upload time
- Supports latest → oldest listing
- Guarantees uniqueness
Example:
IMAGE#2026-01-15T10:45:00Z#img_789



---

## Core Item Type – Image Metadata

Each image is represented as **one item**.

### Attributes

| Attribute | Type | Description |
|---------|------|------------|
| PK | String | `USER#<user_id>` |
| SK | String | `IMAGE#<created_at>#<image_id>` |
| image_id | String | Unique image identifier |
| user_id | String | Owner of the image |
| s3_bucket | String | S3 bucket name |
| s3_folder | String | S3 folder path (images/user_id={user_id}/image_id={image_id}) |
| s3_prefix | String | Same as s3_folder |
| content_type | String | image/jpeg, image/png |
| size_bytes | Number | Original image size |
| width | Number | Image width in pixels |
| height | Number | Image height in pixels |
| aspect_ratio | String | Example: 4:3 |
| visibility | String | public / private / followers |
| tags | List | Used for filtering |
| description | String | Image description |
| created_at | String | ISO-8601 timestamp |
| variants | List | Available image variants (original, medium, thumbnail) |
| processing_status | String | pending / completed |
| likes_count | Number | Engagement metric |
| comments_count | Number | Engagement metric |
| is_deleted | Boolean | Soft delete flag |

---

## Global Secondary Indexes (GSIs)

### GSI-1: Tag-Based Listing (Latest First)

**Purpose**
- Filter images by tag
- Support latest → oldest ordering

GSI1PK = TAG#<tag>
GSI1SK = <created_at>#<image_id>

### (Optional) GSI-2: Public Feed

**Purpose**
- Instagram-style public feed

    GSI2PK = VISIBILITY#public
    GSI2SK = <created_at>#<image_id>

---
