# TRAXORA Test Framework User Guide

This guide provides practical instructions for using the TRAXORA testing system effectively.

## Quick Start

```bash
# Basic test with 50 records
python test_data_generator.py -d 2025-05-20 -c 50

# Run validation
python validate_test_data.py

# Advanced test with all edge cases
python test_data_generator.py -d 2025-05-20 -c 50 --include-duplicates --include-null-divisions --include-overnight-shifts --include-null-assets
```

## Common Test Scenarios

### 1. Standard Attendance Check

Tests basic attendance flagging without complex edge cases:

```bash
python test_data_generator.py -d 2025-05-20 -c 100
```

### 2. Duplicate Driver Detection

Tests how the system handles the same driver appearing on multiple assets:

```bash
python test_data_generator.py -d 2025-05-20 -c 100 --include-duplicates
```

### 3. Missing Data Resilience

Tests system handling of incomplete records:

```bash
python test_data_generator.py -d 2025-05-20 -c 100 --include-null-divisions --include-null-assets
```

### 4. Overnight Shift Testing

Tests time calculations for shifts spanning midnight:

```bash
python test_data_generator.py -d 2025-05-20 -c 100 --include-overnight-shifts
```

## Interpreting Validation Results

The validation results in `validation_results.json` contain:

- **is_valid**: Overall pass/fail result
- **errors**: Critical issues that must be fixed
- **warnings**: Non-critical issues worth investigating
- **statistics**: Detailed metrics about the processed data

## Known Limitations

1. Next-day time markers like `(+1)` require special handling in the time parser
2. Some malformed asset labels may cause driver extraction issues
3. Very large datasets (>1000 records) may slow down validation

## Troubleshooting

If validation fails:

1. Check time format warnings in the console output
2. Verify correct parsing of overnight shifts
3. Inspect duplicate driver detection
4. Look for asset label parsing issues

## Tips for Effective Testing

- Use smaller datasets (50-100 records) for quick iteration
- Test with specific dates that match production data
- Include all edge cases for thorough regression testing
- Save problematic test files for future regression testing