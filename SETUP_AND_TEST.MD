<!--
Author: Vivek Kuumar Goswami
Date: January 15, 2026
-->

# Image Service API - Setup & Testing

Complete guide for setup, deployment, and testing on LocalStack.

---

## Prerequisites & Installation

**Install required tools:**
```bash
pip install aws-sam-cli localstack boto3
```

**Verify installations:**
```bash
sam --version
localstack --version
docker ps  # Ensure Docker is running
```

---

## 1. Start LocalStack

```bash
localstack start -d
localstack status services
```

---

## 2. Set Credentials

**PowerShell:**
```powershell
$env:AWS_ACCESS_KEY_ID = "test"
$env:AWS_SECRET_ACCESS_KEY = "test"
$env:AWS_DEFAULT_REGION = "us-east-1"
```

**Command Prompt:**
```cmd
set AWS_ACCESS_KEY_ID=test
set AWS_SECRET_ACCESS_KEY=test
set AWS_DEFAULT_REGION=us-east-1
```

**Bash/Linux:**
```bash
export AWS_ACCESS_KEY_ID=test
export AWS_SECRET_ACCESS_KEY=test
export AWS_DEFAULT_REGION=us-east-1
```

---

## 3. Create a bucket for artifcats

```bash

aws s3 mb s3://sam-artifacts
```
---


## 3. Build & Deploy

```bash
cd c:\Users\vivek\nerd\imageservice

sam build

sam deploy `
  --stack-name image-service-stack `
  --region us-east-1 `
  --s3-bucket sam-artifacts `
  --capabilities CAPABILITY_IAM `
  --no-confirm-changeset `
  --endpoint-url http://localhost:4566

---

## 4. Start API

```bash
sam local start-api
```

API runs on `http://127.0.0.1:3000` (keep this terminal open)

---

## 5. Test Endpoints (New Terminal)

### Upload Image
```bash
curl -X POST http://127.0.0.1:3000/images `
  -H "Content-Type: application/json" `
  -d '{"user_id":"user123","tags":["test"],"description":"Test"}'
```

Response: `201 Created` with `image_id`

### List Images
```bash
curl -X GET "http://127.0.0.1:3000/images?user_id=user123"
```

Response: `200 OK` with image array

### Wait for Processing
```bash
Start-Sleep -Seconds 5
```

Then list again to see variants completed.

### Get Image with URLs
```bash
curl -X GET "http://127.0.0.1:3000/images/IMAGE_ID"
```

Replace `IMAGE_ID` with the id from upload.

Response: `200 OK` with `download_urls` for all 3 variants

### Filter by Tag
```bash
curl -X GET "http://127.0.0.1:3000/images?user_id=user123&tag=test"
```

### Delete Image
```bash
curl -X DELETE "http://127.0.0.1:3000/images/IMAGE_ID"
```

Response: `204 No Content`

### Verify Deletion
```bash
curl -X GET "http://127.0.0.1:3000/images?user_id=user123"
```

Should be empty.

---

## Test Lambda Functions Directly

```bash
sam local invoke ImageUploadFunction --event events/upload-event.json
sam local invoke ImageListFunction --event events/list-event.json
sam local invoke ImageGetFunction --event events/get-event.json
sam local invoke ImageDeleteFunction --event events/delete-event.json
sam local invoke ImageProcessorFunction --event events/processor-event.json
```

---

## Verify Deployment

```bash
# Check DynamoDB table
aws dynamodb list-tables --endpoint-url http://localhost:4566 --region us-east-1

# Check S3 bucket
aws s3 ls --endpoint-url http://localhost:4566

# Check Lambda functions
aws lambda list-functions --endpoint-url http://localhost:4566 --region us-east-1
```

---

## Troubleshooting

### Port 3000 in use?
```bash
sam local start-api --port 5000
# Use http://127.0.0.1:5000 instead
```

### DynamoDB table not found?
```bash
sam deploy --endpoint-url http://localhost:4566 --stack-name image-service-stack --region us-east-1 --no-confirm-changeset
```

### Docker not running?
Start Docker Desktop or run: `sudo systemctl start docker`

### Check logs
Look at Terminal 1 (where `sam local start-api` runs) for error messages.

---

## Cleanup

```bash
# Stop API (Ctrl+C in Terminal 1)

# Delete stack
aws cloudformation delete-stack `
  --stack-name image-service-stack `
  --endpoint-url http://localhost:4566 `
  --region us-east-1

# Stop LocalStack
localstack stop
```

---

## Quick Reference

| Command | Purpose |
|---------|---------|
| `localstack start -d` | Start LocalStack |
| `sam build` | Build application |
| `sam deploy --endpoint-url http://localhost:4566 --stack-name image-service-stack --region us-east-1 --no-confirm-changeset --capabilities CAPABILITY_IAM` | Deploy to LocalStack |
| `sam local start-api` | Start API server |
| `curl -X POST http://127.0.0.1:3000/images ...` | Upload image |
| `curl -X GET http://127.0.0.1:3000/images?user_id=user123` | List images |
| `curl -X GET http://127.0.0.1:3000/images/IMAGE_ID` | Get image |
| `curl -X DELETE http://127.0.0.1:3000/images/IMAGE_ID` | Delete image |
| `localstack stop` | Stop LocalStack |

---

## Data Model

**DynamoDB Table**: `ImageService`
- **PK**: `USER#{user_id}`
- **SK**: `IMAGE#{created_at}#{image_id}`

**S3 Structure**:
```
s3://image-service-bucket/images/user_id={user_id}/image_id={image_id}/
├── original.jpg
├── medium.jpg (1024x1024)
└── thumbnail.jpg (200x200)
```

**Key Fields**:
- `s3_folder`: S3 path
- `variants`: ["original", "medium", "thumbnail"]
- `processing_status`: "pending" | "completed"
- `width`, `height`: Image dimensions
- `aspect_ratio`: e.g., "4:3"

---

## API Endpoints

| Method | Path | Handler | Response |
|--------|------|---------|----------|
| POST | /images | upload.py | 201 Created |
| GET | /images | list.py | 200 OK (array) |
| GET | /images/{image_id} | get.py | 200 OK (with URLs) |
| DELETE | /images/{image_id} | delete.py | 204 No Content |

---

**Next**: See [ARCHITECTURE.MD](ARCHITECTURE.MD) for system design or [DynamoDB.MD](DynamoDB.MD) for schema details.
