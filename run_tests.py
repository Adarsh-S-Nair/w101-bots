#!/usr/bin/env python3
"""
Test runner for the w101-bots project
"""
import unittest
import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def run_tests():
    """Run all unit tests"""
    # Discover and run tests
    loader = unittest.TestLoader()
    start_dir = 'tests/unit'
    suite = loader.discover(start_dir, pattern='test_*.py')
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Return exit code based on test results
    return 0 if result.wasSuccessful() else 1

if __name__ == '__main__':
    exit_code = run_tests()
    sys.exit(exit_code)
