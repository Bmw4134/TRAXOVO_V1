"""
Enhanced Attendance Module with Payroll Integration
Optimized data structures and seamless geofencing integration
"""
from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from sqlalchemy import Column, Integer, String, DateTime, Float, Boolean, ForeignKey, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from datetime import datetime, timedelta, time
import pandas as pd
import json
import os
from typing import Dict, List, Optional

# Enhanced Database Models
Base = declarative_base()

class Employee(Base):
    __tablename__ = 'employees'
    
    id = Column(Integer, primary_key=True)
    employee_id = Column(String(50), unique=True, nullable=False)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    email = Column(String(150))
    phone = Column(String(20))
    department = Column(String(100))
    job_title = Column(String(100))
    hourly_rate = Column(Float, default=0.0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    attendance_records = relationship("AttendanceRecord", back_populates="employee")
    geofence_logs = relationship("GeofenceLog", back_populates="employee")

class AttendanceRecord(Base):
    __tablename__ = 'attendance_records'
    
    id = Column(Integer, primary_key=True)
    employee_id = Column(String(50), ForeignKey('employees.employee_id'), nullable=False)
    work_date = Column(DateTime, nullable=False)
    clock_in_time = Column(DateTime)
    clock_out_time = Column(DateTime)
    break_start = Column(DateTime)
    break_end = Column(DateTime)
    lunch_start = Column(DateTime)
    lunch_end = Column(DateTime)
    
    # Calculated fields
    regular_hours = Column(Float, default=0.0)
    overtime_hours = Column(Float, default=0.0)
    total_hours = Column(Float, default=0.0)
    
    # Location and equipment
    job_site = Column(String(200))
    equipment_used = Column(String(500))  # JSON string of equipment IDs
    gps_clock_in_lat = Column(Float)
    gps_clock_in_lng = Column(Float)
    gps_clock_out_lat = Column(Float)
    gps_clock_out_lng = Column(Float)
    
    # Status and validation
    status = Column(String(50), default='active')  # active, approved, disputed, corrected
    is_payroll_exported = Column(Boolean, default=False)
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    employee = relationship("Employee", back_populates="attendance_records")

class GeofenceZone(Base):
    __tablename__ = 'geofence_zones'
    
    id = Column(Integer, primary_key=True)
    zone_name = Column(String(200), nullable=False)
    zone_type = Column(String(50))  # job_site, office, restricted
    center_lat = Column(Float, nullable=False)
    center_lng = Column(Float, nullable=False)
    radius_meters = Column(Float, default=100.0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class GeofenceLog(Base):
    __tablename__ = 'geofence_logs'
    
    id = Column(Integer, primary_key=True)
    employee_id = Column(String(50), ForeignKey('employees.employee_id'), nullable=False)
    zone_id = Column(Integer, ForeignKey('geofence_zones.id'), nullable=False)
    event_type = Column(String(20))  # enter, exit
    event_timestamp = Column(DateTime, nullable=False)
    latitude = Column(Float)
    longitude = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    employee = relationship("Employee", back_populates="geofence_logs")
    zone = relationship("GeofenceZone")

class AttendanceEngine:
    """Enhanced attendance processing engine"""
    
    def __init__(self, db_session):
        self.session = db_session
    
    def process_attendance_import(self, file_path: str) -> Dict:
        """Process attendance data from CSV/Excel with validation"""
        try:
            # Load data
            if file_path.endswith('.csv'):
                df = pd.read_csv(file_path)
            else:
                df = pd.read_excel(file_path)
            
            # Standardize columns
            df.columns = df.columns.str.lower().str.replace(' ', '_')
            
            processed_records = []
            errors = []
            
            for index, row in df.iterrows():
                try:
                    # Extract and validate employee
                    employee_id = str(row.get('employee_id', '')).strip()
                    if not employee_id:
                        errors.append(f"Row {index + 2}: Missing employee_id")
                        continue
                    
                    # Parse dates and times
                    work_date = pd.to_datetime(row.get('date', row.get('work_date')), errors='coerce')
                    if pd.isna(work_date):
                        errors.append(f"Row {index + 2}: Invalid work date")
                        continue
                    
                    clock_in = self._parse_time(row.get('clock_in', ''), work_date)
                    clock_out = self._parse_time(row.get('clock_out', ''), work_date)
                    
                    # Calculate hours
                    hours_data = self._calculate_hours(clock_in, clock_out)
                    
                    # Create attendance record
                    attendance_record = AttendanceRecord(
                        employee_id=employee_id,
                        work_date=work_date,
                        clock_in_time=clock_in,
                        clock_out_time=clock_out,
                        regular_hours=hours_data['regular_hours'],
                        overtime_hours=hours_data['overtime_hours'],
                        total_hours=hours_data['total_hours'],
                        job_site=str(row.get('job_site', '')).strip(),
                        equipment_used=str(row.get('equipment_used', '')).strip(),
                        gps_clock_in_lat=row.get('clock_in_lat'),
                        gps_clock_in_lng=row.get('clock_in_lng'),
                        gps_clock_out_lat=row.get('clock_out_lat'),
                        gps_clock_out_lng=row.get('clock_out_lng'),
                        notes=str(row.get('notes', '')).strip()
                    )
                    
                    processed_records.append(attendance_record)
                    
                except Exception as e:
                    errors.append(f"Row {index + 2}: {str(e)}")
            
            # Bulk insert successful records
            if processed_records:
                self.session.add_all(processed_records)
                self.session.commit()
            
            return {
                'success': True,
                'processed_count': len(processed_records),
                'error_count': len(errors),
                'errors': errors
            }
            
        except Exception as e:
            self.session.rollback()
            return {
                'success': False,
                'error': str(e),
                'processed_count': 0
            }
    
    def _parse_time(self, time_str: str, work_date: datetime) -> Optional[datetime]:
        """Parse time string and combine with work date"""
        if not time_str or pd.isna(time_str):
            return None
        
        try:
            # Handle various time formats
            time_str = str(time_str).strip()
            
            # Parse time
            if ':' in time_str:
                time_parts = time_str.split(':')
                hour = int(time_parts[0])
                minute = int(time_parts[1]) if len(time_parts) > 1 else 0
                
                # Handle AM/PM
                if 'pm' in time_str.lower() and hour < 12:
                    hour += 12
                elif 'am' in time_str.lower() and hour == 12:
                    hour = 0
                
                return work_date.replace(hour=hour, minute=minute, second=0, microsecond=0)
            
        except Exception:
            pass
        
        return None
    
    def _calculate_hours(self, clock_in: Optional[datetime], clock_out: Optional[datetime]) -> Dict:
        """Calculate regular and overtime hours"""
        if not clock_in or not clock_out:
            return {'regular_hours': 0.0, 'overtime_hours': 0.0, 'total_hours': 0.0}
        
        # Calculate total hours
        total_hours = (clock_out - clock_in).total_seconds() / 3600
        
        # Standard work day is 8 hours
        regular_hours = min(total_hours, 8.0)
        overtime_hours = max(0.0, total_hours - 8.0)
        
        return {
            'regular_hours': round(regular_hours, 2),
            'overtime_hours': round(overtime_hours, 2),
            'total_hours': round(total_hours, 2)
        }
    
    def generate_payroll_export(self, start_date: datetime, end_date: datetime, format_type: str = 'csv') -> str:
        """Generate payroll export file"""
        # Query attendance records for date range
        records = self.session.query(AttendanceRecord).filter(
            AttendanceRecord.work_date >= start_date,
            AttendanceRecord.work_date <= end_date,
            AttendanceRecord.is_payroll_exported == False
        ).join(Employee).all()
        
        # Prepare export data
        export_data = []
        for record in records:
            export_data.append({
                'Employee_ID': record.employee_id,
                'Employee_Name': f"{record.employee.first_name} {record.employee.last_name}",
                'Work_Date': record.work_date.strftime('%Y-%m-%d'),
                'Clock_In': record.clock_in_time.strftime('%H:%M') if record.clock_in_time else '',
                'Clock_Out': record.clock_out_time.strftime('%H:%M') if record.clock_out_time else '',
                'Regular_Hours': record.regular_hours,
                'Overtime_Hours': record.overtime_hours,
                'Total_Hours': record.total_hours,
                'Hourly_Rate': record.employee.hourly_rate,
                'Regular_Pay': record.regular_hours * record.employee.hourly_rate,
                'Overtime_Pay': record.overtime_hours * record.employee.hourly_rate * 1.5,
                'Total_Pay': (record.regular_hours * record.employee.hourly_rate) + 
                           (record.overtime_hours * record.employee.hourly_rate * 1.5),
                'Job_Site': record.job_site,
                'Equipment_Used': record.equipment_used
            })
        
        # Create DataFrame and export
        df = pd.DataFrame(export_data)
        
        # Generate filename
        filename = f"payroll_export_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}"
        
        if format_type.lower() == 'excel':
            filepath = f"exports/{filename}.xlsx"
            df.to_excel(filepath, index=False)
        else:
            filepath = f"exports/{filename}.csv"
            df.to_csv(filepath, index=False)
        
        # Mark records as exported
        for record in records:
            record.is_payroll_exported = True
        self.session.commit()
        
        return filepath
    
    def validate_geofence_attendance(self, employee_id: str, work_date: datetime) -> Dict:
        """Validate attendance against geofence data"""
        # Get attendance record
        attendance = self.session.query(AttendanceRecord).filter(
            AttendanceRecord.employee_id == employee_id,
            AttendanceRecord.work_date == work_date
        ).first()
        
        if not attendance:
            return {'valid': False, 'reason': 'No attendance record found'}
        
        # Get geofence logs for the day
        geofence_logs = self.session.query(GeofenceLog).filter(
            GeofenceLog.employee_id == employee_id,
            GeofenceLog.event_timestamp >= work_date,
            GeofenceLog.event_timestamp < work_date + timedelta(days=1)
        ).order_by(GeofenceLog.event_timestamp).all()
        
        if not geofence_logs:
            return {'valid': False, 'reason': 'No geofence data available'}
        
        # Validate clock-in location
        first_entry = geofence_logs[0]
        clock_in_valid = abs((attendance.clock_in_time - first_entry.event_timestamp).total_seconds()) <= 300  # 5 min tolerance
        
        # Validate clock-out location
        last_exit = geofence_logs[-1]
        clock_out_valid = abs((attendance.clock_out_time - last_exit.event_timestamp).total_seconds()) <= 300
        
        return {
            'valid': clock_in_valid and clock_out_valid,
            'clock_in_valid': clock_in_valid,
            'clock_out_valid': clock_out_valid,
            'geofence_entries': len([log for log in geofence_logs if log.event_type == 'enter']),
            'geofence_exits': len([log for log in geofence_logs if log.event_type == 'exit'])
        }

# Flask Blueprint for Attendance Module
attendance_bp = Blueprint('attendance', __name__, url_prefix='/attendance')

@attendance_bp.route('/')
def attendance_dashboard():
    """Main attendance dashboard"""
    return render_template('attendance/dashboard.html')

@attendance_bp.route('/import', methods=['GET', 'POST'])
def import_attendance():
    """Import attendance data from file"""
    if request.method == 'POST':
        # Handle file upload and processing
        file = request.files.get('attendance_file')
        if file and file.filename:
            # Save file temporarily
            temp_path = f"temp/{file.filename}"
            os.makedirs('temp', exist_ok=True)
            file.save(temp_path)
            
            # Process with attendance engine
            from app import db
            engine = AttendanceEngine(db.session)
            result = engine.process_attendance_import(temp_path)
            
            # Clean up temp file
            os.remove(temp_path)
            
            if result['success']:
                flash(f"Successfully processed {result['processed_count']} attendance records", 'success')
            else:
                flash(f"Import failed: {result.get('error', 'Unknown error')}", 'error')
            
            return redirect(url_for('attendance.attendance_dashboard'))
    
    return render_template('attendance/import.html')

@attendance_bp.route('/export-payroll')
def export_payroll():
    """Export attendance data for payroll"""
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    format_type = request.args.get('format', 'csv')
    
    if start_date and end_date:
        start_date = datetime.strptime(start_date, '%Y-%m-%d')
        end_date = datetime.strptime(end_date, '%Y-%m-%d')
        
        from app import db
        engine = AttendanceEngine(db.session)
        filepath = engine.generate_payroll_export(start_date, end_date, format_type)
        
        return jsonify({
            'success': True,
            'file_path': filepath,
            'download_url': f"/downloads/{os.path.basename(filepath)}"
        })
    
    return jsonify({'success': False, 'error': 'Invalid date range'})

@attendance_bp.route('/validate-geofence/<employee_id>/<work_date>')
def validate_geofence(employee_id, work_date):
    """Validate attendance against geofence data"""
    work_date = datetime.strptime(work_date, '%Y-%m-%d')
    
    from app import db
    engine = AttendanceEngine(db.session)
    validation_result = engine.validate_geofence_attendance(employee_id, work_date)
    
    return jsonify(validation_result)

@attendance_bp.route('/api/attendance-summary')
def attendance_summary():
    """API endpoint for attendance summary data"""
    from app import db
    
    # Get current week's summary
    today = datetime.now().date()
    week_start = today - timedelta(days=today.weekday())
    week_end = week_start + timedelta(days=6)
    
    summary = db.session.query(AttendanceRecord).filter(
        AttendanceRecord.work_date >= week_start,
        AttendanceRecord.work_date <= week_end
    ).all()
    
    total_hours = sum(record.total_hours for record in summary)
    total_employees = len(set(record.employee_id for record in summary))
    
    return jsonify({
        'total_hours': total_hours,
        'total_employees': total_employees,
        'records_count': len(summary),
        'week_start': week_start.isoformat(),
        'week_end': week_end.isoformat()
    })