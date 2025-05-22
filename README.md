# TRAXORA Fleet Management System

A cutting-edge fleet management platform leveraging multi-agent intelligent systems to optimize equipment deployment and operational efficiency through advanced data processing and real-time insights.

## GENIUS CORE Architecture

The TRAXORA system implements a modular multi-agent architecture called "GENIUS CORE" (Groundworks Equipment Network Intelligent Operational Utility System - Consolidated Operational Reporting Engine) that enables robust data processing, validation, and reporting.

### Key Components

- **Dual-Mode Framework**: Supports simultaneous development and production environments
- **Modular Agents**: Specialized modules that handle specific tasks in the data pipeline
- **Cross-Module Validation**: Ensures data integrity through multi-source verification
- **Geospatial Intelligence**: Advanced location-based analytics and validation
- **Dynamic Reporting Engine**: Configurable report generation with multiple output formats

## Modular Agents

The system uses a series of specialized agents that work together to process and validate data:

1. **Driver Classifier Agent** (`agents/driver_classifier_agent.py`)
   - Analyzes driver activity data
   - Filters based on vehicle type and job site assignment
   - Classifies drivers according to operational criteria

2. **Geo Validator Agent** (`agents/geo_validator_agent.py`)
   - Validates locations against job site boundaries
   - Performs geospatial calculations and distance measurements
   - Provides confidence scores for location-based validations

3. **Report Generator Agent** (`agents/report_generator_agent.py`)
   - Creates comprehensive reports from processed data
   - Supports multiple report types (driver, job site, compliance)
   - Generates summary statistics and performance metrics

4. **Output Formatter Agent** (`agents/output_formatter_agent.py`)
   - Transforms report data into various output formats (JSON, CSV, HTML, etc.)
   - Applies styling and visualization enhancements
   - Manages file output and distribution

## Usage

Each agent can be used independently or as part of the integrated pipeline:

```python
# Example: Using the driver classifier agent
from agents.driver_classifier_agent import handle as classify_drivers

driver_data = [...]  # Your driver data
results = classify_drivers(driver_data)
```

## Configuration

System configuration is managed through YAML files:

- `dev_config.yaml`: Development environment configuration
- `prod_config.yaml`: Production environment configuration

Runtime mode is determined by the `runtime_mode.py` module, which loads the appropriate configuration and agent implementations.

## Database Structure

The database schema is initialized and managed by `init_db.py`, which creates the necessary tables for assets, drivers, job sites, and activity records.

## Log Files

Agent activity and system events are logged to:

- `logs/agent_usage.log`: Agent usage statistics
- `logs/system.log`: System-level events and errors

## MTD Reporting

The system includes enhanced Month-to-Date reporting capabilities:

- Processes real CSV data from multiple sources
- Filters for specific vehicle types (pickup trucks, on-road vehicles)
- Removes zero-value entries for cleaner reports
- Cross-validates data across multiple input sources