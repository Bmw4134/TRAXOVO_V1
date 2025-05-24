# TRAXORA Fleet Management System - Development Assistance Request

I'm building a fleet management dashboard called TRAXORA with these key capabilities:

1. **Driver Attendance Tracking**
   - Process CSV data from GaugeSmart telematics (May 18-24, 2025)
   - Classify drivers as "On Time", "Late Start", "Early End", or "Not On Job"
   - Generate weekly summary reports with attendance trends

2. **Technical Stack**
   - Python/Flask backend with SQLAlchemy database
   - Bootstrap UI with responsive design
   - CSV parsing with field mapping for handling inconsistent column names

3. **Current Implementation**
   - Core processing works but CSV field mapping needs improvement
   - Classification logic uses time-based rules (7:30AM cutoff for late, 4:00PM cutoff for early end)
   - Field mapping handles column name variations (Driver/Contact/Driver Name)

4. **Current Challenges**
   - Need better strategies for mapping inconsistent CSV column names (sometimes "Driver", sometimes "Contact")
   - Need to improve classification logic for edge cases
   - Need to optimize for larger datasets
   - Want to enhance visualizations with more actionable insights

I need guidance on:
1. Best practices for robust CSV field mapping
2. Performance optimization tips for processing 5000+ rows
3. Recommendations for enhancing the classification logic
4. Suggestions for better data visualizations
5. Security best practices for sensitive driver data

Any technical advice, code improvements, or architectural guidance would be appreciated!