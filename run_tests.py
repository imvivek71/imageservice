#!/usr/bin/env python
"""
Test runner script for Image Service API
Provides convenient commands for running different test suites
"""

import subprocess
import sys
import os


def run_command(cmd, description):
    """Run a command and report results."""
    print(f"\n{'='*60}")
    print(f"Running: {description}")
    print(f"{'='*60}")
    result = subprocess.run(cmd, shell=True)
    return result.returncode == 0


def main():
    """Main test runner."""
    if len(sys.argv) < 2:
        print("""
Usage: python run_tests.py <command>

Commands:
  all              - Run all tests
  unit             - Run only unit tests
  integration      - Run only integration tests
  coverage         - Run tests with coverage report
  handlers         - Run handler tests only
  services         - Run service tests only
  utils            - Run utility tests only
  fast             - Run tests (skip slow tests)
  verbose          - Run tests in verbose mode
  watch            - Run tests in watch mode (requires pytest-watch)
  specific <name>  - Run specific test file (e.g., test_handlers_upload.py)

Examples:
  python run_tests.py all
  python run_tests.py coverage
  python run_tests.py specific test_handlers_upload.py
        """)
        return 1
    
    command = sys.argv[1]
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    commands = {
        'all': ('pytest tests/', 'All Tests'),
        'unit': ('pytest tests/ -m "not integration"', 'Unit Tests'),
        'integration': ('pytest tests/test_integration.py -v', 'Integration Tests'),
        'coverage': ('pytest tests/ --cov=src --cov-report=html --cov-report=term', 'Tests with Coverage'),
        'handlers': ('pytest tests/test_handlers_*.py -v', 'Handler Tests'),
        'services': ('pytest tests/test_*_service.py -v', 'Service Tests'),
        'utils': ('pytest tests/test_utils.py -v', 'Utility Tests'),
        'fast': ('pytest tests/ -m "not slow"', 'Fast Tests'),
        'verbose': ('pytest tests/ -vv', 'Verbose Tests'),
        'watch': ('pytest-watch tests/', 'Watch Mode Tests'),
    }
    
    if command == 'specific' and len(sys.argv) > 2:
        test_file = sys.argv[2]
        cmd = f'pytest tests/{test_file} -v'
        return 0 if run_command(cmd, f'Test: {test_file}') else 1
    
    if command in commands:
        cmd, desc = commands[command]
        return 0 if run_command(cmd, desc) else 1
    
    print(f"Unknown command: {command}")
    return 1


if __name__ == '__main__':
    sys.exit(main())
