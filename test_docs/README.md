# Test Suite Documentation

## Quick Links

- **[Quick Start Guide](#quick-start)** - 3 commands to get started
- **[Running Tests](#running-tests)** - How to execute tests
- **[Test Coverage](#test-coverage)** - What's tested
- **[Test Structure](#test-structure)** - File organization
- **[Debugging](#debugging)** - Troubleshooting
- **[CI/CD Integration](#cicd-integration)** - Integration examples

---

## Quick Start

### Installation
```bash
pip install -r requirements-test.txt
```

### Run All Tests
```bash
pytest
```

### Run with Coverage
```bash
pytest --cov=src --cov-report=html
```

---

## Running Tests

### Common Commands

```bash
# All tests
pytest

# Verbose output
pytest -v

# Stop on first failure
pytest -x

# Show print statements
pytest -s

# Specific test file
pytest tests/test_handlers_upload.py

# Specific test class
pytest tests/test_handlers_upload.py::TestUploadHandler

# Specific test method
pytest tests/test_handlers_upload.py::TestUploadHandler::test_upload_success
```

### By Category

```bash
# Handler tests only
pytest tests/test_handlers_*.py

# Service tests only
pytest tests/test_*_service.py

# Integration tests
pytest tests/test_integration.py

# Utils tests
pytest tests/test_utils.py
```

### Coverage Reports

```bash
# Generate coverage report
pytest --cov=src --cov-report=html

# View in browser
open htmlcov/index.html
```

### Using Test Runner Script

```bash
python run_tests.py all              # All tests
python run_tests.py coverage         # Coverage report
python run_tests.py handlers         # Handler tests only
python run_tests.py services         # Service tests only
python run_tests.py integration      # Integration tests
python run_tests.py specific <file>  # Specific file
python run_tests.py verbose          # Verbose output
```

---

## Test Coverage

### By Component

**Services (27 tests)**
- DynamoDB Service: 9 tests (put, get, query, scan, update, delete)
- S3 Service: 8 tests (upload, download, delete, presigned URL)
- Image Service: 10 tests (find, filtering, URL generation, deletion)

**Handlers (27 tests)**
- Upload Handler: 5 tests (success, validation, errors)
- List Handler: 8 tests (list, filtering, errors)
- Get Handler: 7 tests (get, validation, not found)
- Delete Handler: 7 tests (delete, validation, hard delete)

**Utilities (13 tests)**
- Decimal Encoding: 4 tests
- Response Functions: 5 tests
- Logger: 4 tests

**Integration (6 tests)**
- Upload → List workflow
- Upload → Get workflow
- Upload → Delete workflow
- User isolation
- Tag filtering
- Visibility filtering

**Total: 63+ test cases**

---

## Test Structure

```
tests/
├── conftest.py                  # Fixtures: AWS mocking, events, context
├── test_dynamodb_service.py     # DynamoDB CRUD tests
├── test_s3_service.py           # S3 upload/download/delete tests
├── test_image_service.py        # Image business logic tests
├── test_handlers_upload.py      # Upload endpoint tests
├── test_handlers_list.py        # List endpoint tests
├── test_handlers_get.py         # Get endpoint tests
├── test_handlers_delete.py      # Delete endpoint tests
├── test_utils.py                # Utility function tests
└── test_integration.py          # Integration workflow tests
```

### Fixtures

All tests use fixtures from `conftest.py`:
- `aws_credentials` - AWS environment setup
- `dynamodb_table` - Mock DynamoDB table
- `s3_bucket` - Mock S3 bucket
- `lambda_context` - Mock Lambda context
- `sample_image_data` - Sample image binary
- Event fixtures: `upload_event`, `list_event`, `get_event`, `delete_event`

### Mocking

- **AWS Services**: Mocked with `moto` library (no real AWS calls)
- **Service Dependencies**: Mocked with `unittest.mock.patch`
- **Logger**: Mocked to prevent console noise

---

## Debugging

### Show Output
```bash
pytest -s
```

### Show Local Variables
```bash
pytest -l
```

### Very Verbose
```bash
pytest -vv
```

### Use Python Debugger
```bash
pytest --pdb
```

### Single Test
```bash
pytest tests/test_file.py::TestClass::test_method -vv -s
```

### Common Issues

**Import errors?**
- Check `sys.path.insert` in conftest.py is correct

**Mock not working?**
- Use full module path: `patch('handlers.upload.image_service')`

**Test isolation issues?**
- Check fixture scopes and cleanup

---

## CI/CD Integration

### GitHub Actions

```yaml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.12'
      - run: pip install -r requirements-test.txt
      - run: pytest tests/ --cov=src --cov-report=xml
      - uses: codecov/codecov-action@v2
```

### GitLab CI

```yaml
test:
  image: python:3.12
  script:
    - pip install -r requirements-test.txt
    - pytest tests/ --cov=src
  coverage: '/TOTAL.*\s+(\d+%)$/'
```

---

## Test Examples

### Testing Success
```python
def test_upload_success(self):
    event = {...}
    with patch('handlers.upload.image_service') as mock:
        mock.generate_download_urls.return_value = {'original': 'url'}
        response = lambda_handler(event, context)
        assert response['statusCode'] == 201
```

### Testing Validation
```python
def test_missing_parameter(self):
    event = {...}  # missing required param
    response = handler(event, context)
    assert response['statusCode'] == 400
```

### Testing Errors
```python
def test_service_error(self):
    with patch('service.method') as mock:
        mock.side_effect = Exception("Error")
        response = handler(event, context)
        assert response['statusCode'] == 500
```

---

## Dependencies

```
pytest>=7.4.0              # Test framework
pytest-cov>=4.1.0         # Coverage reporting
pytest-mock>=3.11.1       # Mock utilities
moto[s3,dynamodb]>=4.2.0  # AWS mocking
boto3>=1.28.0             # AWS SDK
botocore>=1.31.0          # AWS definitions
```

Optional:
```
pytest-watch              # Watch mode
pytest-xdist              # Parallel execution
pytest-timeout            # Test timeouts
```

---

## Key Features

✅ **63+ test cases** covering all functionality  
✅ **Complete mocking** - no real AWS calls  
✅ **Fast execution** - <10 seconds for full suite  
✅ **Production ready** - best practices followed  
✅ **Well isolated** - tests are independent  
✅ **Easy to extend** - clear patterns  

---

## Next Steps

1. Install: `pip install -r requirements-test.txt`
2. Run: `pytest`
3. Check coverage: `pytest --cov=src --cov-report=html`
4. Review: `htmlcov/index.html`
5. Integrate with CI/CD

---

**Status**: ✅ Complete and Production Ready
