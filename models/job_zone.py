"""
Job Zone and Working Hours Models for TRAXORA

This module contains models for tracking job zone information and working hours.
Job zones are specific geographical areas where work is performed, and working hours
define when work should be performed at each zone.
"""
from datetime import datetime, time
from app import db
from sqlalchemy import ForeignKey, UniqueConstraint

class JobZone(db.Model):
    """
    Job Zone model for tracking work locations with defined boundaries
    """
    __tablename__ = 'job_zones'
    
    id = db.Column(db.Integer, primary_key=True)
    job_site_id = db.Column(db.Integer, db.ForeignKey('job_sites.id'), nullable=False)
    name = db.Column(db.String(128), nullable=False)
    description = db.Column(db.Text)
    
    # Geofence boundary (simplified rectangle for MVP)
    latitude_min = db.Column(db.Float, nullable=False)
    latitude_max = db.Column(db.Float, nullable=False)
    longitude_min = db.Column(db.Float, nullable=False)
    longitude_max = db.Column(db.Float, nullable=False)
    
    # Zone characteristics
    active = db.Column(db.Boolean, default=True)
    zone_type = db.Column(db.String(64), default='work')  # 'work', 'storage', 'maintenance', etc.
    priority = db.Column(db.Integer, default=1)  # Priority level when multiple zones are applicable
    
    # Metadata
    organization_id = db.Column(db.Integer, db.ForeignKey('organizations.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    job_site = db.relationship('JobSite', backref='job_zones')
    working_hours = db.relationship('JobZoneWorkingHours', back_populates='job_zone', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<JobZone {self.name} at {self.job_site.name}>'
    
    def is_point_in_zone(self, latitude, longitude):
        """
        Check if a point is within this job zone
        
        Args:
            latitude (float): Latitude of the point
            longitude (float): Longitude of the point
            
        Returns:
            bool: True if the point is within the zone, False otherwise
        """
        return (
            self.latitude_min <= latitude <= self.latitude_max and
            self.longitude_min <= longitude <= self.longitude_max
        )
    
    def get_current_working_hours(self, date=None):
        """
        Get the working hours for the specified date or today
        
        Args:
            date (datetime.date, optional): The date to get working hours for
            
        Returns:
            JobZoneWorkingHours: The working hours for the specified date or None
        """
        if date is None:
            date = datetime.utcnow().date()
            
        # First try to find specific working hours for this date
        specific_hours = JobZoneWorkingHours.query.filter_by(
            job_zone_id=self.id,
            date=date,
            is_override=True
        ).first()
        
        if specific_hours:
            return specific_hours
        
        # If no specific hours, get the default working hours for the day of week
        day_of_week = date.weekday()  # 0=Monday, 6=Sunday
        default_hours = JobZoneWorkingHours.query.filter_by(
            job_zone_id=self.id,
            day_of_week=day_of_week,
            is_override=False
        ).first()
        
        return default_hours


class JobZoneWorkingHours(db.Model):
    """
    Working hours for a job zone
    """
    __tablename__ = 'job_zone_working_hours'
    
    id = db.Column(db.Integer, primary_key=True)
    job_zone_id = db.Column(db.Integer, db.ForeignKey('job_zones.id'), nullable=False)
    
    # Either day_of_week or specific date must be set
    day_of_week = db.Column(db.Integer, nullable=True)  # 0=Monday, 6=Sunday
    date = db.Column(db.Date, nullable=True)  # Specific date for override
    is_override = db.Column(db.Boolean, default=False)  # True if this is a one-time override
    
    # Working hours
    start_time = db.Column(db.Time, nullable=False, default=time(8, 0))  # 8:00 AM
    end_time = db.Column(db.Time, nullable=False, default=time(17, 0))   # 5:00 PM
    
    # Break periods
    break_start = db.Column(db.Time, nullable=True)
    break_end = db.Column(db.Time, nullable=True)
    lunch_start = db.Column(db.Time, nullable=True)
    lunch_end = db.Column(db.Time, nullable=True)
    
    # Status
    is_working_day = db.Column(db.Boolean, default=True)  # False for holidays/closures
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    job_zone = db.relationship('JobZone', back_populates='working_hours')
    
    # Constraints
    __table_args__ = (
        # Either day_of_week or date must be non-null, but not both
        UniqueConstraint('job_zone_id', 'day_of_week', name='_job_zone_day_of_week_uc'),
        UniqueConstraint('job_zone_id', 'date', name='_job_zone_date_uc'),
    )
    
    def __repr__(self):
        if self.is_override:
            return f'<JobZoneWorkingHours for {self.job_zone.name} on {self.date}>'
        else:
            days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            return f'<JobZoneWorkingHours for {self.job_zone.name} on {days[self.day_of_week]}>'
    
    def is_time_within_working_hours(self, check_time=None):
        """
        Check if the given time is within working hours
        
        Args:
            check_time (datetime.time, optional): The time to check
            
        Returns:
            bool: True if the time is within working hours, False otherwise
        """
        if not self.is_working_day:
            return False
            
        if check_time is None:
            check_time = datetime.utcnow().time()
            
        # Check if time is within work hours
        if not (self.start_time <= check_time <= self.end_time):
            return False
            
        # Check if time is during break
        if self.break_start and self.break_end:
            if self.break_start <= check_time <= self.break_end:
                return False
                
        # Check if time is during lunch
        if self.lunch_start and self.lunch_end:
            if self.lunch_start <= check_time <= self.lunch_end:
                return False
                
        return True
        
    def get_total_working_minutes(self):
        """
        Calculate the total working minutes in this period
        
        Returns:
            int: Total working minutes
        """
        if not self.is_working_day:
            return 0
            
        # Calculate total work day length in minutes
        start_minutes = self.start_time.hour * 60 + self.start_time.minute
        end_minutes = self.end_time.hour * 60 + self.end_time.minute
        total_minutes = end_minutes - start_minutes
        
        # Subtract break time
        if self.break_start and self.break_end:
            break_start_minutes = self.break_start.hour * 60 + self.break_start.minute
            break_end_minutes = self.break_end.hour * 60 + self.break_end.minute
            total_minutes -= (break_end_minutes - break_start_minutes)
            
        # Subtract lunch time
        if self.lunch_start and self.lunch_end:
            lunch_start_minutes = self.lunch_start.hour * 60 + self.lunch_start.minute
            lunch_end_minutes = self.lunch_end.hour * 60 + self.lunch_end.minute
            total_minutes -= (lunch_end_minutes - lunch_start_minutes)
            
        return max(0, total_minutes)


class JobZoneActivity(db.Model):
    """
    Record of activity within a job zone
    """
    __tablename__ = 'job_zone_activities'
    
    id = db.Column(db.Integer, primary_key=True)
    job_zone_id = db.Column(db.Integer, db.ForeignKey('job_zones.id'), nullable=False)
    asset_id = db.Column(db.Integer, db.ForeignKey('assets.id'), nullable=False)
    driver_id = db.Column(db.Integer, db.ForeignKey('drivers.id'), nullable=True)
    
    # Activity details
    entry_time = db.Column(db.DateTime, nullable=False)
    exit_time = db.Column(db.DateTime, nullable=True)  # Null if still in zone
    
    # Location at entry
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    
    # Activity metrics
    duration_minutes = db.Column(db.Integer)  # Updated when exit_time is set
    is_within_working_hours = db.Column(db.Boolean)
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    job_zone = db.relationship('JobZone')
    asset = db.relationship('Asset')
    driver = db.relationship('Driver')
    
    def __repr__(self):
        return f'<JobZoneActivity {self.asset.asset_identifier} in {self.job_zone.name}>'
    
    def complete_activity(self, exit_time=None):
        """
        Complete this activity by setting the exit time and calculating duration
        
        Args:
            exit_time (datetime, optional): The exit time
            
        Returns:
            int: Duration in minutes
        """
        if exit_time is None:
            exit_time = datetime.utcnow()
            
        self.exit_time = exit_time
        
        # Calculate duration in minutes
        duration = (exit_time - self.entry_time).total_seconds() / 60
        self.duration_minutes = int(duration)
        
        return self.duration_minutes