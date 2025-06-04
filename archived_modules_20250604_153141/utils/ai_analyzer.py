"""
AI Analysis Module

This module uses OpenAI's GPT models to analyze fleet data and generate insights.
"""
import os
import json
import logging
from datetime import datetime, timedelta
from openai import OpenAI
from flask import current_app
from app import db
from models.reports import Driver, DriverAttendance, Jobsite, WorkZoneHours, EquipmentBilling

# Configure logging
logger = logging.getLogger(__name__)

# Initialize OpenAI client
try:
    client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
    logger.info("OpenAI client initialized successfully")
except Exception as e:
    logger.error(f"Error initializing OpenAI client: {e}")
    client = None

def analyze_driver_attendance(driver_id=None, days=30):
    """
    Analyze driver attendance patterns and generate insights
    
    Args:
        driver_id: Optional driver ID to focus analysis on
        days: Number of days to analyze (default: 30)
    
    Returns:
        dict: Analysis results
    """
    if not client:
        return {"error": "OpenAI client not available"}
    
    try:
        # Get date range
        end_date = datetime.today().date()
        start_date = end_date - timedelta(days=days)
        
        # Build query
        query = db.session.query(
            DriverAttendance,
            Driver
        ).join(
            Driver, DriverAttendance.driver_id == Driver.id
        ).filter(
            DriverAttendance.date.between(start_date, end_date)
        )
        
        # Filter by driver if specified
        if driver_id:
            query = query.filter(DriverAttendance.driver_id == driver_id)
        
        # Execute query
        attendance_records = query.all()
        
        if not attendance_records:
            return {"error": "No attendance records found"}
        
        # Prepare data for analysis
        driver_data = {}
        for record, driver in attendance_records:
            if driver.id not in driver_data:
                driver_data[driver.id] = {
                    "name": driver.name,
                    "records": [],
                    "stats": {
                        "total_days": 0,
                        "late_starts": 0,
                        "early_ends": 0,
                        "no_jobsites": 0,
                        "total_hours": 0,
                        "billable_hours": 0
                    }
                }
            
            # Add record
            driver_data[driver.id]["records"].append({
                "date": record.date.isoformat() if record.date else None,
                "late_start": record.late_start,
                "early_end": record.early_end,
                "no_jobsite": record.no_jobsite,
                "total_hours": record.total_hours,
                "billable_hours": record.billable_hours,
                "jobsite": record.jobsite.name if record.jobsite else None
            })
            
            # Update stats
            driver_data[driver.id]["stats"]["total_days"] += 1
            driver_data[driver.id]["stats"]["late_starts"] += 1 if record.late_start else 0
            driver_data[driver.id]["stats"]["early_ends"] += 1 if record.early_end else 0
            driver_data[driver.id]["stats"]["no_jobsites"] += 1 if record.no_jobsite else 0
            driver_data[driver.id]["stats"]["total_hours"] += record.total_hours or 0
            driver_data[driver.id]["stats"]["billable_hours"] += record.billable_hours or 0
        
        # Generate prompt for OpenAI
        prompt = f"""Analyze the following driver attendance data from {start_date} to {end_date}:
        
{json.dumps(driver_data, indent=2)}

Please provide the following insights:
1. Identify any concerning attendance patterns for each driver
2. Calculate the efficiency (billable hours / total hours) for each driver
3. Suggest improvements for drivers with attendance issues
4. Highlight the best performing drivers and what makes them successful

Format your response as JSON with the following structure:
{{
  "overview": "A general summary of all drivers' attendance",
  "driver_insights": [
    {{
      "driver_id": "ID of the driver",
      "name": "Name of the driver",
      "efficiency": "Efficiency percentage",
      "patterns": "Identified attendance patterns",
      "concerns": "Any attendance concerns",
      "suggestions": "Improvement suggestions"
    }}
  ],
  "top_performers": ["List of top performing drivers"],
  "areas_of_concern": ["List of specific areas that need attention"]
}}
"""
        
        # Call OpenAI API
        response = client.chat.completions.create(
            model="gpt-4o",  # the newest OpenAI model is "gpt-4o" which was released May 13, 2024
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.5,
            max_tokens=2000
        )
        
        # Parse and return results
        try:
            analysis = json.loads(response.choices[0].message.content)
            return analysis
        except json.JSONDecodeError:
            return {"error": "Invalid JSON response from OpenAI"}
        
    except Exception as e:
        logger.error(f"Error analyzing driver attendance: {e}")
        return {"error": f"Analysis failed: {str(e)}"}

def analyze_workzone_efficiency(jobsite_id=None, days=30):
    """
    Analyze work zone efficiency and generate insights
    
    Args:
        jobsite_id: Optional jobsite ID to focus analysis on
        days: Number of days to analyze (default: 30)
    
    Returns:
        dict: Analysis results
    """
    if not client:
        return {"error": "OpenAI client not available"}
    
    try:
        # Get date range
        end_date = datetime.today().date()
        start_date = end_date - timedelta(days=days)
        
        # Build query
        query = db.session.query(
            WorkZoneHours,
            Jobsite
        ).join(
            Jobsite, WorkZoneHours.jobsite_id == Jobsite.id
        ).filter(
            WorkZoneHours.date.between(start_date, end_date)
        )
        
        # Filter by jobsite if specified
        if jobsite_id:
            query = query.filter(WorkZoneHours.jobsite_id == jobsite_id)
        
        # Execute query
        workzone_records = query.all()
        
        if not workzone_records:
            return {"error": "No work zone records found"}
        
        # Prepare data for analysis
        jobsite_data = {}
        for record, jobsite in workzone_records:
            if jobsite.id not in jobsite_data:
                jobsite_data[jobsite.id] = {
                    "name": jobsite.name,
                    "code": jobsite.code,
                    "location": {
                        "latitude": jobsite.latitude,
                        "longitude": jobsite.longitude
                    },
                    "records": [],
                    "stats": {
                        "total_days": 0,
                        "total_hours": 0,
                        "equipment_hours": 0,
                        "labor_hours": 0,
                        "expected_hours": 0
                    }
                }
            
            # Add record
            jobsite_data[jobsite.id]["records"].append({
                "date": record.date.isoformat() if record.date else None,
                "total_hours": record.total_hours,
                "equipment_hours": record.equipment_hours,
                "labor_hours": record.labor_hours,
                "expected_hours": record.expected_hours,
                "efficiency": record.efficiency_percentage
            })
            
            # Update stats
            jobsite_data[jobsite.id]["stats"]["total_days"] += 1
            jobsite_data[jobsite.id]["stats"]["total_hours"] += record.total_hours or 0
            jobsite_data[jobsite.id]["stats"]["equipment_hours"] += record.equipment_hours or 0
            jobsite_data[jobsite.id]["stats"]["labor_hours"] += record.labor_hours or 0
            jobsite_data[jobsite.id]["stats"]["expected_hours"] += record.expected_hours or 0
        
        # Calculate overall efficiency for each jobsite
        for jobsite_id, data in jobsite_data.items():
            if data["stats"]["expected_hours"] > 0:
                data["stats"]["overall_efficiency"] = (data["stats"]["total_hours"] / data["stats"]["expected_hours"]) * 100
            else:
                data["stats"]["overall_efficiency"] = 0
        
        # Generate prompt for OpenAI
        prompt = f"""Analyze the following work zone efficiency data from {start_date} to {end_date}:
        
{json.dumps(jobsite_data, indent=2)}

Please provide the following insights:
1. Identify high and low performing work zones based on efficiency
2. Analyze the relationship between equipment hours and labor hours
3. Suggest improvements for work zones with low efficiency
4. Identify any trends or patterns in the data

Format your response as JSON with the following structure:
{{
  "overview": "A general summary of work zone efficiency",
  "jobsite_insights": [
    {{
      "jobsite_id": "ID of the jobsite",
      "name": "Name of the jobsite",
      "efficiency": "Overall efficiency percentage",
      "patterns": "Identified efficiency patterns",
      "concerns": "Any efficiency concerns",
      "suggestions": "Improvement suggestions"
    }}
  ],
  "top_performers": ["List of top performing jobsites"],
  "bottom_performers": ["List of lowest performing jobsites"],
  "equipment_labor_ratio": "Analysis of equipment to labor hour ratios",
  "recommendations": ["List of specific recommendations to improve efficiency"]
}}
"""
        
        # Call OpenAI API
        response = client.chat.completions.create(
            model="gpt-4o",  # the newest OpenAI model is "gpt-4o" which was released May 13, 2024
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.5,
            max_tokens=2000
        )
        
        # Parse and return results
        try:
            analysis = json.loads(response.choices[0].message.content)
            return analysis
        except json.JSONDecodeError:
            return {"error": "Invalid JSON response from OpenAI"}
        
    except Exception as e:
        logger.error(f"Error analyzing work zone efficiency: {e}")
        return {"error": f"Analysis failed: {str(e)}"}

def analyze_equipment_billing(category=None, months=6):
    """
    Analyze equipment billing and generate insights
    
    Args:
        category: Optional equipment category to focus analysis on
        months: Number of months to analyze (default: 6)
    
    Returns:
        dict: Analysis results
    """
    if not client:
        return {"error": "OpenAI client not available"}
    
    try:
        # Get date range
        today = datetime.today()
        end_date = today.date()
        
        # Generate list of (year, month) tuples for the last 'months'
        date_range = []
        for i in range(months):
            month = today.month - i
            year = today.year
            while month <= 0:
                month += 12
                year -= 1
            date_range.append((year, month))
        
        # Build base query
        query = db.session.query(
            EquipmentBilling,
            Asset
        ).join(
            Asset, EquipmentBilling.asset_id == Asset.id
        )
        
        # Apply date range filter
        query = query.filter(
            (EquipmentBilling.year == date_range[0][0]) & (EquipmentBilling.month == date_range[0][1])
        )
        
        for year, month in date_range[1:]:
            query = query.or_(
                (EquipmentBilling.year == year) & (EquipmentBilling.month == month)
            )
        
        # Apply category filter if specified
        if category:
            query = query.filter(EquipmentBilling.category == category)
        
        # Execute query
        billing_records = query.all()
        
        if not billing_records:
            return {"error": "No billing records found"}
        
        # Prepare data for analysis
        asset_data = {}
        for record, asset in billing_records:
            if asset.id not in asset_data:
                asset_data[asset.id] = {
                    "identifier": asset.asset_identifier,
                    "category": asset.asset_category,
                    "make": asset.asset_make,
                    "model": asset.asset_model,
                    "records": [],
                    "stats": {
                        "total_months": 0,
                        "total_hours": 0,
                        "total_amount": 0
                    }
                }
            
            # Add record
            asset_data[asset.id]["records"].append({
                "year": record.year,
                "month": record.month,
                "category": record.category,
                "hours_used": record.hours_used,
                "rate": record.rate,
                "total_amount": record.total_amount
            })
            
            # Update stats
            asset_data[asset.id]["stats"]["total_months"] += 1
            asset_data[asset.id]["stats"]["total_hours"] += record.hours_used or 0
            asset_data[asset.id]["stats"]["total_amount"] += record.total_amount or 0
        
        # Calculate average rate for each asset
        for asset_id, data in asset_data.items():
            if data["stats"]["total_hours"] > 0:
                data["stats"]["avg_rate"] = data["stats"]["total_amount"] / data["stats"]["total_hours"]
            else:
                data["stats"]["avg_rate"] = 0
        
        # Generate prompt for OpenAI
        prompt = f"""Analyze the following equipment billing data for the past {months} months:
        
{json.dumps(asset_data, indent=2)}

Please provide the following insights:
1. Identify the most and least cost-effective equipment
2. Analyze utilization patterns (hours used vs. cost)
3. Suggest optimization strategies to reduce equipment costs
4. Identify any unusual billing patterns or outliers

Format your response as JSON with the following structure:
{{
  "overview": "A general summary of equipment billing",
  "asset_insights": [
    {{
      "asset_id": "ID of the asset",
      "identifier": "Asset identifier",
      "category": "Asset category",
      "avg_rate": "Average hourly rate",
      "cost_effectiveness": "Assessment of cost effectiveness",
      "utilization": "Assessment of utilization",
      "suggestions": "Cost optimization suggestions"
    }}
  ],
  "most_cost_effective": ["List of most cost-effective assets"],
  "least_cost_effective": ["List of least cost-effective assets"],
  "outliers": ["List of assets with unusual billing patterns"],
  "recommendations": ["List of specific recommendations to optimize equipment costs"]
}}
"""
        
        # Call OpenAI API
        response = client.chat.completions.create(
            model="gpt-4o",  # the newest OpenAI model is "gpt-4o" which was released May 13, 2024
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.5,
            max_tokens=2000
        )
        
        # Parse and return results
        try:
            analysis = json.loads(response.choices[0].message.content)
            return analysis
        except json.JSONDecodeError:
            return {"error": "Invalid JSON response from OpenAI"}
        
    except Exception as e:
        logger.error(f"Error analyzing equipment billing: {e}")
        return {"error": f"Analysis failed: {str(e)}"}

def generate_executive_summary(days=30):
    """
    Generate an executive summary of fleet operations
    
    Args:
        days: Number of days to analyze (default: 30)
    
    Returns:
        dict: Summary results
    """
    if not client:
        return {"error": "OpenAI client not available"}
    
    try:
        # Get date range
        end_date = datetime.today().date()
        start_date = end_date - timedelta(days=days)
        
        # Collect attendance data
        attendance_stats = db.session.query(
            func.count(DriverAttendance.id).label('total_records'),
            func.sum(DriverAttendance.total_hours).label('total_hours'),
            func.sum(DriverAttendance.billable_hours).label('billable_hours'),
            func.sum(func.cast(DriverAttendance.late_start, db.Integer)).label('late_starts'),
            func.sum(func.cast(DriverAttendance.early_end, db.Integer)).label('early_ends'),
            func.sum(func.cast(DriverAttendance.no_jobsite, db.Integer)).label('no_jobsites')
        ).filter(
            DriverAttendance.date.between(start_date, end_date)
        ).first()
        
        # Collect work zone data
        workzone_stats = db.session.query(
            func.count(WorkZoneHours.id).label('total_records'),
            func.sum(WorkZoneHours.total_hours).label('total_hours'),
            func.sum(WorkZoneHours.equipment_hours).label('equipment_hours'),
            func.sum(WorkZoneHours.labor_hours).label('labor_hours'),
            func.sum(WorkZoneHours.expected_hours).label('expected_hours')
        ).filter(
            WorkZoneHours.date.between(start_date, end_date)
        ).first()
        
        # Collect billing data
        billing_stats = db.session.query(
            func.count(EquipmentBilling.id).label('total_records'),
            func.sum(EquipmentBilling.hours_used).label('total_hours'),
            func.sum(EquipmentBilling.total_amount).label('total_amount')
        ).join(
            Asset, EquipmentBilling.asset_id == Asset.id
        ).first()
        
        # Calculate derived metrics
        attendance_efficiency = 0
        if attendance_stats and attendance_stats.total_hours and attendance_stats.total_hours > 0:
            attendance_efficiency = (attendance_stats.billable_hours / attendance_stats.total_hours) * 100
        
        workzone_efficiency = 0
        if workzone_stats and workzone_stats.expected_hours and workzone_stats.expected_hours > 0:
            workzone_efficiency = (workzone_stats.total_hours / workzone_stats.expected_hours) * 100
        
        avg_hourly_cost = 0
        if billing_stats and billing_stats.total_hours and billing_stats.total_hours > 0:
            avg_hourly_cost = billing_stats.total_amount / billing_stats.total_hours
        
        # Prepare data for analysis
        summary_data = {
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "days": days
            },
            "attendance": {
                "total_records": attendance_stats.total_records if attendance_stats else 0,
                "total_hours": float(attendance_stats.total_hours) if attendance_stats and attendance_stats.total_hours else 0,
                "billable_hours": float(attendance_stats.billable_hours) if attendance_stats and attendance_stats.billable_hours else 0,
                "efficiency": float(attendance_efficiency),
                "late_starts": attendance_stats.late_starts if attendance_stats else 0,
                "early_ends": attendance_stats.early_ends if attendance_stats else 0,
                "no_jobsites": attendance_stats.no_jobsites if attendance_stats else 0
            },
            "workzone": {
                "total_records": workzone_stats.total_records if workzone_stats else 0,
                "total_hours": float(workzone_stats.total_hours) if workzone_stats and workzone_stats.total_hours else 0,
                "equipment_hours": float(workzone_stats.equipment_hours) if workzone_stats and workzone_stats.equipment_hours else 0,
                "labor_hours": float(workzone_stats.labor_hours) if workzone_stats and workzone_stats.labor_hours else 0,
                "expected_hours": float(workzone_stats.expected_hours) if workzone_stats and workzone_stats.expected_hours else 0,
                "efficiency": float(workzone_efficiency)
            },
            "billing": {
                "total_records": billing_stats.total_records if billing_stats else 0,
                "total_hours": float(billing_stats.total_hours) if billing_stats and billing_stats.total_hours else 0,
                "total_amount": float(billing_stats.total_amount) if billing_stats and billing_stats.total_amount else 0,
                "avg_hourly_cost": float(avg_hourly_cost)
            }
        }
        
        # Get top performers
        top_drivers = db.session.query(
            Driver.id,
            Driver.name,
            func.sum(DriverAttendance.billable_hours).label('billable_hours'),
            func.sum(DriverAttendance.total_hours).label('total_hours')
        ).join(
            DriverAttendance, Driver.id == DriverAttendance.driver_id
        ).filter(
            DriverAttendance.date.between(start_date, end_date)
        ).group_by(
            Driver.id, Driver.name
        ).order_by(
            (func.sum(DriverAttendance.billable_hours) / func.sum(DriverAttendance.total_hours)).desc()
        ).limit(3).all()
        
        summary_data["top_drivers"] = [{
            "id": driver.id,
            "name": driver.name,
            "billable_hours": float(driver.billable_hours) if driver.billable_hours else 0,
            "total_hours": float(driver.total_hours) if driver.total_hours else 0,
            "efficiency": (float(driver.billable_hours) / float(driver.total_hours) * 100) if driver.total_hours and driver.total_hours > 0 else 0
        } for driver in top_drivers]
        
        # Generate prompt for OpenAI
        prompt = f"""Generate an executive summary of fleet operations for the period from {start_date} to {end_date} based on the following data:
        
{json.dumps(summary_data, indent=2)}

Please provide the following:
1. A concise executive summary of overall fleet performance
2. Key highlights and concerns across driver attendance, work zone efficiency, and equipment billing
3. Actionable recommendations for improvement
4. Projected cost savings if recommendations are implemented

Format your response as JSON with the following structure:
{{
  "executive_summary": "A concise summary of fleet performance",
  "key_metrics": {{
    "driver_efficiency": "Analysis of driver attendance efficiency",
    "workzone_efficiency": "Analysis of work zone efficiency",
    "equipment_costs": "Analysis of equipment costs and utilization"
  }},
  "highlights": ["List of key positive highlights"],
  "concerns": ["List of key concerns or issues"],
  "recommendations": ["List of actionable recommendations"],
  "projected_savings": "Estimated cost savings from implementing recommendations",
  "conclusion": "Brief concluding statement"
}}
"""
        
        # Call OpenAI API
        response = client.chat.completions.create(
            model="gpt-4o",  # the newest OpenAI model is "gpt-4o" which was released May 13, 2024
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.7,
            max_tokens=2000
        )
        
        # Parse and return results
        try:
            analysis = json.loads(response.choices[0].message.content)
            return analysis
        except json.JSONDecodeError:
            return {"error": "Invalid JSON response from OpenAI"}
        
    except Exception as e:
        logger.error(f"Error generating executive summary: {e}")
        return {"error": f"Summary generation failed: {str(e)}"}