# Tests

This directory contains unit tests for the w101-bots project.

## Running Tests

To run all tests:
```bash
python run_tests.py
```

To run tests with verbose output:
```bash
python -m unittest discover tests/unit -v
```

## Test Structure

- `unit/` - Unit tests for individual components
  - `automation/` - Tests for automation modules
    - `test_trivia_positioning.py` - Tests for the feedback-based positioning system

## Test Coverage

The tests cover:
- Question positioning detection and adjustment
- Third/fourth answer positioning detection and adjustment
- Combined positioning scenarios
- Position calculations with various adjustments
- Integration testing of the complete positioning flow

## Key Test Scenarios

1. **Question Positioning Off**: When the first answer attempt copies the question text instead of an answer
2. **Third/Fourth Positioning Off**: When third/fourth answers copy the same text as the previous answer
3. **Combined Issues**: Both question positioning and third/fourth positioning issues occurring together
4. **No Adjustments Needed**: Normal case where all positioning is correct
