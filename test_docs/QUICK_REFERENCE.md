# Quick Reference

## Most Used Commands

```bash
pytest                                      # Run all tests
pytest -v                                   # Verbose
pytest --cov=src                           # With coverage
pytest tests/test_handlers_upload.py        # Specific file
pytest -k upload                           # Tests containing "upload"
pytest -x                                  # Stop on first failure
pytest -s                                  # Show print statements
```

## Using Test Runner

```bash
python run_tests.py all                    # All tests
python run_tests.py coverage               # Coverage report
python run_tests.py handlers               # Handler tests
python run_tests.py services               # Service tests
python run_tests.py integration            # Integration tests
```

## Test Files

| File | Tests | Purpose |
|------|-------|---------|
| conftest.py | - | Fixtures & setup |
| test_dynamodb_service.py | 9 | DynamoDB operations |
| test_s3_service.py | 8 | S3 operations |
| test_image_service.py | 10 | Image business logic |
| test_handlers_upload.py | 5 | Upload endpoint |
| test_handlers_list.py | 8 | List endpoint |
| test_handlers_get.py | 7 | Get endpoint |
| test_handlers_delete.py | 7 | Delete endpoint |
| test_utils.py | 13 | Utilities |
| test_integration.py | 6 | Workflows |

## Setup

```bash
pip install -r requirements-test.txt
```

## What's Tested

- ✅ Upload (5 tests)
- ✅ List (8 tests)
- ✅ Get (7 tests)
- ✅ Delete (7 tests)
- ✅ Services (27 tests)
- ✅ Utilities (13 tests)
- ✅ Integration (6 tests)

**Total: 73 tests**

## Coverage

```bash
# Generate
pytest --cov=src --cov-report=html

# View
open htmlcov/index.html
```

## Debugging

```bash
pytest -vv              # Very verbose
pytest --pdb           # Python debugger
pytest -s              # Show output
pytest -l              # Show local vars
pytest tests/file.py::Class::test_method  # Single test
```

## Error Paths

```bash
pytest -k "error"      # Error-related tests
pytest -k "missing"    # Missing parameter tests
pytest -k "not_found"  # Not found tests
```

## Fixtures

Available in all tests:
- `aws_credentials` - AWS setup
- `dynamodb_table` - Mock DynamoDB
- `s3_bucket` - Mock S3
- `lambda_context` - Mock context
- `upload_event`, `list_event`, `get_event`, `delete_event`

## Performance

- Execution time: <10 seconds
- No real AWS calls
- All tests isolated
- Can run in parallel

## More Help

See [README.md](README.md) for complete documentation.
