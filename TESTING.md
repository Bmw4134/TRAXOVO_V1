# TRAXORA - Testing Framework Documentation

## Overview

This document provides comprehensive information about the testing framework for the TRAXORA fleet management system. It explains available tools, test data generation, validation methods, and best practices for ensuring system reliability.

## Table of Contents

1. [Test Data Generator](#test-data-generator)
2. [Validation Framework](#validation-framework)
3. [End-to-End Testing](#end-to-end-testing)
4. [Edge Case Testing](#edge-case-testing)
5. [Best Practices](#best-practices)

## Test Data Generator

The `test_data_generator.py` script creates realistic mock data for testing the attendance reporting system.

### Basic Usage

```bash
python test_data_generator.py -d 2025-05-20 -c 100 -o mock_data.csv
```

### Parameters

- `-d, --date`: Date for records (YYYY-MM-DD format)
- `-c, --count`: Number of records to generate (default: 100)
- `-o, --output`: Output file path (default: mock_data_test.csv)
- `-r, --random`: Use a random date instead of specified date

### Advanced Edge Case Testing

Special flags enable generating complex edge cases:

- `--include-duplicates`: Generate duplicate employee IDs across multiple assets
- `--include-null-divisions`: Include drivers with missing division/region data
- `--include-overnight-shifts`: Create shifts that span midnight (next-day)
- `--include-null-assets`: Generate missing or malformed asset labels

Example with all edge cases:

```bash
python test_data_generator.py -d 2025-05-20 --include-duplicates --include-null-divisions --include-overnight-shifts --include-null-assets -c 50
```

### Data Scenarios

The generator creates these scenarios in controlled proportions:

1. **Normal on-time drivers** (35% of total)
2. **Late start drivers** (15% of total) - Late by 16-60 minutes
3. **Early end drivers** (15% of total) - Early by 16-90 minutes
4. **Missing start/end time** (10% of total) - Either start or end missing
5. **Double issue drivers** (5% of total) - Both late and early
6. **No times at all** (5% of total) - Both start and end missing
7. **Overnight shifts** (5% of total when enabled) - Shifts crossing midnight
8. **Miscellaneous edge cases** (remainder) - Various special cases:
   - Very late/early times
   - Malformed asset labels
   - Multiple driver names
   - Timezone-included times
   - Missing assets and drivers
   - Next-day markers

## Validation Framework

The `validate_test_data.py` script processes test data and validates it for consistency and accuracy.

### Usage

```bash
python validate_test_data.py
```

### Validation Checks

The validation system performs these key checks:

1. **Mathematical consistency** - Ensures all counts match between summary and details
2. **Driver uniqueness** - Identifies duplicate drivers across different assets
3. **Issue categorization** - Verifies correct categorization of attendance issues
4. **Statistical integrity** - Confirms all statistical totals are consistent
5. **Multiple issues** - Validates correct handling of drivers with multiple issues

### Output

The script generates:

- `report_data.json` - Processed attendance data
- `validation_results.json` - Validation results and statistics
- Console output with validation summary

## End-to-End Testing

The system includes a complete end-to-end testing approach:

1. Generate test data with `test_data_generator.py`
2. Process the data with the attendance processor
3. Validate the results with `validate_test_data.py`

### Example Test Flow

```bash
# Generate test data
python test_data_generator.py -d 2025-05-20 -c 100

# Process and validate
python validate_test_data.py
```

## Edge Case Testing

The testing framework specifically handles these important edge cases:

### 1. Cross-Asset Driver Normalization

Tests how the system handles the same driver appearing across multiple assets. This verifies:
- Driver identity resolution across different equipment
- Correct attendance tracking for drivers with multiple assignments
- Proper aggregation in statistics and reports

### 2. Missing Division/Region Data

Tests system resilience with incomplete division data, verifying:
- UI properly renders without division information
- Reports correctly handle missing region data
- System doesn't break with incomplete hierarchical information

### 3. Overnight Shifts

Tests time-related logic for shifts spanning midnight:
- Parsing of next-day markers like `(+1)` and `(Next Day)`
- Proper calculation of shift durations across day boundaries
- Correct attendance flagging for overnight workers

### 4. Missing/Malformed Asset Information

Tests system robustness with problematic asset data:
- Empty asset labels
- Malformed asset-driver combinations
- Generic placeholders like "UNKNOWN"
- Invalid characters in asset data

## Best Practices

### When to Run Tests

- Before major deployments
- After making changes to the attendance processor
- When modifying time calculation logic
- After changes to driver/asset data handling
- During regression testing cycles

### Test Data Volume Guidelines

- **Small tests**: 20-50 records (quick verification)
- **Medium tests**: 100-200 records (standard testing)
- **Large tests**: 500+ records (performance testing)

### Test Data Retention

It's recommended to save test data files for regression testing, especially those that exposed bugs or edge cases, along with their validation results.

## Conclusion

This testing framework provides comprehensive tools for validating the TRAXORA fleet management system. By leveraging the test data generator with various edge cases and the validation system, you can ensure robust, reliable operation of the attendance reporting module.