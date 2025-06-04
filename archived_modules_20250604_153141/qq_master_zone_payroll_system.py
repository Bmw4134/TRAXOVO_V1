"""
QQ Master Zone and Payroll System
Enhanced version integrated with TRAXOVO attendance and Fort Worth operations
"""
import json
import hashlib
import time
import sqlite3
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone
from dataclasses import dataclass

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ZoneEntry:
    """Zone registry entry"""
    key: str
    name: str
    lat: float
    lon: float
    created_at: str
    last_used: str

@dataclass
class AttendanceEntry:
    """Attendance log entry"""
    user: str
    clock_in: int
    clock_out: int
    zone_id: str
    duration: int
    hash: str
    payroll_amount: float
    created_at: str

class QQMasterZonePayrollSystem:
    """
    Enhanced QQ Master Zone and Payroll System
    Integrated with TRAXOVO Fort Worth operations
    """
    
    def __init__(self):
        # Enhanced database storage instead of JSON files
        self.db_path = "qq_master_zone_payroll.db"
        
        # Legacy JSON file paths for compatibility
        self.log_path = Path("qq_master_log.json")
        self.zone_registry_path = Path("zone_registry.json")
        self.payroll_log_path = Path("payroll_log.json")
        
        # Fort Worth specific zones
        self.fort_worth_zones = {
            "fort_worth_yard": {"name": "Fort Worth Main Yard", "lat": 32.7767, "lon": -97.3298},
            "downtown_site": {"name": "Downtown Construction Site", "lat": 32.7555, "lon": -97.3308},
            "alliance_depot": {"name": "Alliance Equipment Depot", "lat": 32.9889, "lon": -97.3189},
            "trinity_river": {"name": "Trinity River Project", "lat": 32.7357, "lon": -97.3095}
        }
        
        self.initialize_system()
        
        logger.info("QQ Master Zone and Payroll System initialized")
    
    def initialize_system(self):
        """Initialize database and legacy JSON files"""
        self.initialize_database()
        self.initialize_legacy_files()
        self.populate_fort_worth_zones()
    
    def initialize_database(self):
        """Initialize SQLite database for enhanced functionality"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Zone registry table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS zone_registry (
                    key TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    lat REAL NOT NULL,
                    lon REAL NOT NULL,
                    zone_type TEXT DEFAULT 'construction',
                    active BOOLEAN DEFAULT TRUE,
                    created_at TEXT NOT NULL,
                    last_used TEXT NOT NULL,
                    usage_count INTEGER DEFAULT 0
                )
            ''')
            
            # Attendance log table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS attendance_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user TEXT NOT NULL,
                    clock_in INTEGER NOT NULL,
                    clock_out INTEGER NOT NULL,
                    zone_id TEXT NOT NULL,
                    duration INTEGER NOT NULL,
                    hash TEXT UNIQUE NOT NULL,
                    payroll_amount REAL NOT NULL,
                    overtime_hours REAL DEFAULT 0,
                    shift_type TEXT DEFAULT 'regular',
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (zone_id) REFERENCES zone_registry (key)
                )
            ''')
            
            # Payroll summary table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS payroll_summary (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user TEXT NOT NULL,
                    zone_id TEXT NOT NULL,
                    total_duration INTEGER NOT NULL,
                    total_amount REAL NOT NULL,
                    entry_count INTEGER NOT NULL,
                    period_start TEXT NOT NULL,
                    period_end TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
            ''')
            
            # Rate configuration table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS rate_config (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    zone_id TEXT NOT NULL,
                    user_role TEXT DEFAULT 'operator',
                    base_rate REAL NOT NULL,
                    overtime_rate REAL NOT NULL,
                    effective_date TEXT NOT NULL,
                    active BOOLEAN DEFAULT TRUE,
                    created_at TEXT NOT NULL
                )
            ''')
            
            conn.commit()
            conn.close()
            logger.info("QQ Master Zone Payroll database initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
    
    def initialize_legacy_files(self):
        """Initialize legacy JSON files for compatibility"""
        for file in [self.log_path, self.zone_registry_path, self.payroll_log_path]:
            if not file.exists():
                initial_data = [] if file != self.zone_registry_path else {}
                file.write_text(json.dumps(initial_data, indent=2))
    
    def populate_fort_worth_zones(self):
        """Populate Fort Worth specific zones"""
        for zone_key, zone_data in self.fort_worth_zones.items():
            zone_id = self.normalize_zone(
                zone_data["name"], 
                zone_data["lat"], 
                zone_data["lon"],
                zone_type="fort_worth_operations"
            )
            logger.debug(f"Fort Worth zone registered: {zone_data['name']} -> {zone_id}")
    
    def hash_string(self, s):
        """Generate SHA-256 hash of string"""
        return hashlib.sha256(s.encode()).hexdigest()
    
    def timestamp(self):
        """Get current timestamp"""
        return int(time.time())
    
    def normalize_zone(self, name, lat, lon, zone_type="construction"):
        """Enhanced zone normalization with database storage"""
        key = self.hash_string(f"{name.lower()}_{round(lat, 3)}_{round(lon, 3)}")
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Check if zone exists
            cursor.execute('SELECT key, usage_count FROM zone_registry WHERE key = ?', (key,))
            result = cursor.fetchone()
            
            if result:
                # Update usage count and last used
                cursor.execute('''
                    UPDATE zone_registry 
                    SET last_used = ?, usage_count = usage_count + 1 
                    WHERE key = ?
                ''', (datetime.now().isoformat(), key))
            else:
                # Create new zone
                cursor.execute('''
                    INSERT INTO zone_registry 
                    (key, name, lat, lon, zone_type, created_at, last_used, usage_count)
                    VALUES (?, ?, ?, ?, ?, ?, ?, 1)
                ''', (key, name, lat, lon, zone_type, 
                      datetime.now().isoformat(), datetime.now().isoformat()))
            
            conn.commit()
            conn.close()
            
            # Update legacy JSON file for compatibility
            self.update_legacy_zone_registry(key, name, lat, lon)
            
            return key
            
        except Exception as e:
            logger.error(f"Error normalizing zone: {e}")
            return key
    
    def update_legacy_zone_registry(self, key, name, lat, lon):
        """Update legacy JSON zone registry"""
        try:
            registry = json.loads(self.zone_registry_path.read_text())
            if key not in registry:
                registry[key] = {"name": name, "lat": lat, "lon": lon}
                self.zone_registry_path.write_text(json.dumps(registry, indent=2))
        except Exception as e:
            logger.error(f"Error updating legacy zone registry: {e}")
    
    def get_rate_for_user_zone(self, user, zone_id):
        """Get appropriate rate for user and zone"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Check for specific rate configuration
            cursor.execute('''
                SELECT base_rate, overtime_rate 
                FROM rate_config 
                WHERE zone_id = ? AND active = TRUE 
                ORDER BY effective_date DESC LIMIT 1
            ''', (zone_id,))
            
            result = cursor.fetchone()
            conn.close()
            
            if result:
                return {"base_rate": result[0], "overtime_rate": result[1]}
            else:
                # Fort Worth default rates
                return {"base_rate": 28.50, "overtime_rate": 42.75}  # 1.5x overtime
                
        except Exception as e:
            logger.error(f"Error getting rate: {e}")
            return {"base_rate": 25.00, "overtime_rate": 37.50}  # Fallback rates
    
    def calculate_payroll(self, user, duration, zone_id):
        """Enhanced payroll calculation with overtime"""
        rates = self.get_rate_for_user_zone(user, zone_id)
        hours = duration / 3600
        
        # Calculate regular and overtime hours
        regular_hours = min(hours, 8)  # Max 8 regular hours per day
        overtime_hours = max(0, hours - 8)
        
        # Calculate amounts
        regular_amount = regular_hours * rates["base_rate"]
        overtime_amount = overtime_hours * rates["overtime_rate"]
        total_amount = regular_amount + overtime_amount
        
        return {
            "regular_hours": regular_hours,
            "overtime_hours": overtime_hours,
            "regular_amount": regular_amount,
            "overtime_amount": overtime_amount,
            "total_amount": round(total_amount, 2)
        }
    
    def log_attendance(self, user, clock_in, clock_out, zone_name, lat, lon, shift_type="regular"):
        """Enhanced attendance logging with database storage"""
        zone_id = self.normalize_zone(zone_name, lat, lon)
        duration = clock_out - clock_in
        
        # Calculate payroll
        payroll_calc = self.calculate_payroll(user, duration, zone_id)
        
        # Create hash for uniqueness
        entry_hash = self.hash_string(f"{user}_{clock_in}_{zone_id}")
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Insert attendance record
            cursor.execute('''
                INSERT INTO attendance_log 
                (user, clock_in, clock_out, zone_id, duration, hash, 
                 payroll_amount, overtime_hours, shift_type, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (user, clock_in, clock_out, zone_id, duration, entry_hash,
                  payroll_calc["total_amount"], payroll_calc["overtime_hours"], 
                  shift_type, datetime.now().isoformat()))
            
            conn.commit()
            conn.close()
            
            # Update legacy JSON files
            self.update_legacy_attendance_log(user, clock_in, clock_out, zone_id, duration, entry_hash)
            self.update_legacy_payroll_log(user, duration, zone_id, payroll_calc["total_amount"])
            
            logger.info(f"Attendance logged: {user} at {zone_name} - ${payroll_calc['total_amount']}")
            
            return {
                "status": "success",
                "entry_hash": entry_hash,
                "payroll": payroll_calc,
                "zone_id": zone_id
            }
            
        except Exception as e:
            logger.error(f"Error logging attendance: {e}")
            return {"status": "error", "message": str(e)}
    
    def update_legacy_attendance_log(self, user, clock_in, clock_out, zone_id, duration, entry_hash):
        """Update legacy JSON attendance log"""
        try:
            log = json.loads(self.log_path.read_text())
            entry = {
                "user": user,
                "clock_in": clock_in,
                "clock_out": clock_out,
                "zone_id": zone_id,
                "duration": duration,
                "hash": entry_hash
            }
            log.append(entry)
            self.log_path.write_text(json.dumps(log, indent=2))
        except Exception as e:
            logger.error(f"Error updating legacy attendance log: {e}")
    
    def update_legacy_payroll_log(self, user, duration, zone_id, amount):
        """Update legacy JSON payroll log"""
        try:
            payroll = json.loads(self.payroll_log_path.read_text())
            payroll.append({
                "user": user,
                "zone_id": zone_id,
                "duration": duration,
                "amount": amount,
                "timestamp": self.timestamp(),
                "hash": self.hash_string(f"{user}_{zone_id}_{duration}")
            })
            self.payroll_log_path.write_text(json.dumps(payroll, indent=2))
        except Exception as e:
            logger.error(f"Error updating legacy payroll log: {e}")
    
    def get_user_attendance_summary(self, user, days=30):
        """Get attendance summary for user"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get attendance records for the last N days
            cutoff_time = self.timestamp() - (days * 24 * 3600)
            
            cursor.execute('''
                SELECT 
                    COUNT(*) as shift_count,
                    SUM(duration) as total_duration,
                    SUM(payroll_amount) as total_pay,
                    SUM(overtime_hours) as total_overtime,
                    AVG(duration) as avg_shift_duration
                FROM attendance_log 
                WHERE user = ? AND clock_in >= ?
            ''', (user, cutoff_time))
            
            result = cursor.fetchone()
            
            # Get zone breakdown
            cursor.execute('''
                SELECT zr.name, COUNT(*) as visits, SUM(al.payroll_amount) as zone_pay
                FROM attendance_log al
                JOIN zone_registry zr ON al.zone_id = zr.key
                WHERE al.user = ? AND al.clock_in >= ?
                GROUP BY al.zone_id, zr.name
                ORDER BY zone_pay DESC
            ''', (user, cutoff_time))
            
            zone_breakdown = cursor.fetchall()
            
            conn.close()
            
            return {
                "user": user,
                "period_days": days,
                "shift_count": result[0] or 0,
                "total_hours": round((result[1] or 0) / 3600, 2),
                "total_pay": round(result[2] or 0, 2),
                "total_overtime_hours": round(result[3] or 0, 2),
                "avg_shift_hours": round(((result[4] or 0) / 3600), 2),
                "zone_breakdown": [
                    {"zone": row[0], "visits": row[1], "pay": round(row[2], 2)}
                    for row in zone_breakdown
                ]
            }
            
        except Exception as e:
            logger.error(f"Error getting user summary: {e}")
            return {"error": str(e)}
    
    def get_zone_utilization_report(self):
        """Get zone utilization report for Fort Worth operations"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Zone utilization over last 30 days
            cutoff_time = self.timestamp() - (30 * 24 * 3600)
            
            cursor.execute('''
                SELECT 
                    zr.name,
                    zr.zone_type,
                    COUNT(al.id) as total_shifts,
                    COUNT(DISTINCT al.user) as unique_workers,
                    SUM(al.duration) as total_duration,
                    SUM(al.payroll_amount) as total_payroll,
                    AVG(al.duration) as avg_shift_duration
                FROM zone_registry zr
                LEFT JOIN attendance_log al ON zr.key = al.zone_id AND al.clock_in >= ?
                WHERE zr.zone_type LIKE '%fort_worth%' OR zr.usage_count > 0
                GROUP BY zr.key, zr.name, zr.zone_type
                ORDER BY total_payroll DESC
            ''', (cutoff_time,))
            
            results = cursor.fetchall()
            conn.close()
            
            return {
                "report_period": "Last 30 days",
                "total_zones": len(results),
                "zones": [
                    {
                        "name": row[0],
                        "type": row[1],
                        "total_shifts": row[2] or 0,
                        "unique_workers": row[3] or 0,
                        "total_hours": round((row[4] or 0) / 3600, 2),
                        "total_payroll": round(row[5] or 0, 2),
                        "avg_shift_hours": round(((row[6] or 0) / 3600), 2)
                    }
                    for row in results
                ]
            }
            
        except Exception as e:
            logger.error(f"Error getting zone utilization: {e}")
            return {"error": str(e)}
    
    def simulate_fort_worth_attendance(self):
        """Simulate realistic Fort Worth attendance data"""
        import random
        
        users = ["alice_rodriguez", "bob_johnson", "carlos_martinez", "diana_smith", "eric_wilson"]
        zones = list(self.fort_worth_zones.keys())
        
        # Generate last 7 days of data
        for day_offset in range(7):
            base_time = self.timestamp() - (day_offset * 24 * 3600)
            
            for user in users:
                if random.random() < 0.9:  # 90% attendance rate
                    # Random start time between 6-8 AM
                    start_hour = random.uniform(6, 8)
                    clock_in = base_time + int(start_hour * 3600)
                    
                    # Random shift duration 7-10 hours
                    shift_hours = random.uniform(7, 10)
                    clock_out = clock_in + int(shift_hours * 3600)
                    
                    # Random zone
                    zone_key = random.choice(zones)
                    zone_data = self.fort_worth_zones[zone_key]
                    
                    self.log_attendance(
                        user, clock_in, clock_out,
                        zone_data["name"],
                        zone_data["lat"],
                        zone_data["lon"]
                    )
        
        logger.info("Fort Worth attendance simulation completed")

def initialize_qq_master_zone_payroll():
    """Initialize QQ Master Zone and Payroll System"""
    global qq_master_system
    qq_master_system = QQMasterZonePayrollSystem()
    
    # Generate some sample data
    qq_master_system.simulate_fort_worth_attendance()
    
    logger.info("QQ Master Zone and Payroll System fully activated")
    return qq_master_system

def get_master_system_status():
    """Get master system status"""
    if 'qq_master_system' in globals() and qq_master_system:
        return {
            "status": "ACTIVE",
            "zones_registered": len(qq_master_system.fort_worth_zones),
            "database_path": qq_master_system.db_path,
            "legacy_files": [
                str(qq_master_system.log_path),
                str(qq_master_system.zone_registry_path),
                str(qq_master_system.payroll_log_path)
            ]
        }
    return {"status": "NOT_INITIALIZED"}

# Global instance
qq_master_system = None

if __name__ == "__main__":
    # Test the system
    system = QQMasterZonePayrollSystem()
    
    # Simulate attendance entry
    result = system.log_attendance(
        "alice_test", 
        system.timestamp() - 3600, 
        system.timestamp(), 
        "Fort Worth Main Yard", 
        32.7767, 
        -97.3298
    )
    
    print("Attendance logged:", json.dumps(result, indent=2))
    
    # Get user summary
    summary = system.get_user_attendance_summary("alice_test", 7)
    print("User summary:", json.dumps(summary, indent=2))
    
    # Get zone utilization
    zones = system.get_zone_utilization_report()
    print("Zone utilization:", json.dumps(zones, indent=2))