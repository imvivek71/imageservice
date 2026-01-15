<!--
Author: Vivek Kuumar Goswami
Date: January 15, 2026
-->

# Image Service API - Roadmap & Architecture

## Overview
This project is a scalable image service backend (like Instagram) supporting image upload, storage, metadata management, and retrieval. It leverages AWS services (API Gateway, Lambda, S3, DynamoDB) and is developed in Python 3.7+ with LocalStack for local development.

## Architecture

- **API Gateway**: Entry point for all API requests.
- **AWS Lambda**: Stateless compute for API logic (upload, list, view, delete).
- **Amazon S3**: Stores image files.
- **DynamoDB**: Stores image metadata (user, timestamp, tags, etc.).
- **LocalStack**: Local AWS cloud stack for development/testing.

### High-Level Flow
1. **Upload Image**: User uploads image + metadata → API Gateway → Lambda → S3 (original.jpg) + DynamoDB (metadata with pending status)
2. **Process Image** (Async): S3 Event triggers Image Processor Lambda → Download original → Create medium & thumbnail → S3 + Update DynamoDB
3. **List Images**: User requests list with filters → API Gateway → Lambda → DynamoDB (query)
4. **View/Download Image**: User requests image → API Gateway → Lambda → S3 (presigned URLs for all variants)
5. **Delete Image**: User requests delete → API Gateway → Lambda → S3 (delete all variants) + DynamoDB (soft delete)

## Roadmap

### 1. API Design
- [ ] Define OpenAPI spec for endpoints:
  - POST `/images` (upload)
  - GET `/images` (list, with filters)
  - GET `/images/{id}` (view/download)
  - DELETE `/images/{id}` (delete)

### 2. Implementation
- [ ] Set up LocalStack (API Gateway, Lambda, S3, DynamoDB)
- [ ] Implement Lambda functions for each endpoint
- [ ] Integrate S3 for image storage
- [ ] Integrate DynamoDB for metadata
- [ ] Add filtering logic (e.g., by user, tag)

### 3. Testing
- [ ] Write unit tests for all Lambda functions
- [ ] Test API flows locally with LocalStack

### 4. Documentation
- [ ] API usage instructions
- [ ] Example requests/responses
- [ ] Local development setup guide

## Example Metadata Schema (DynamoDB)

| Attribute         | Type    | Description                        |
|-------------------|---------|------------------------------------|
| PK                | String  | USER#<user_id>                     |
| SK                | String  | IMAGE#<created_at>#<image_id>      |
| image_id          | String  | Unique image identifier            |
| user_id           | String  | Owner of the image                 |
| s3_bucket         | String  | S3 bucket name                     |
| s3_folder         | String  | S3 folder path                     |
| s3_prefix         | String  | Same as s3_folder                  |
| content_type      | String  | image/jpeg, image/png              |
| size_bytes        | Number  | Original image size                |
| width             | Number  | Image width in pixels              |
| height            | Number  | Image height in pixels             |
| aspect_ratio      | String  | Example: 4:3                       |
| visibility        | String  | public / private / followers       |
| tags              | List    | Used for filtering                 |
| description       | String  | Image description                  |
| created_at        | String  | ISO-8601 timestamp                 |
| variants          | List    | [original, medium, thumbnail]      |
| processing_status | String  | pending / completed                |
| likes_count       | Number  | Engagement metric                  |
| comments_count    | Number  | Engagement metric                  |
| is_deleted        | Boolean | Soft delete flag                   |

## Scalability Considerations
- Stateless Lambdas for horizontal scaling
- S3 and DynamoDB scale automatically
- Use presigned URLs for secure, scalable image access
- API Gateway throttling and caching

---

*Update this file as the project evolves. See README.MD for setup and usage details.*
