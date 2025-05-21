# Make individual models available at the package level
from models.user import User
from models.asset import Asset
from models.driver import Driver
from models.asset_driver_mapping import AssetDriverMapping
from models.job_site import JobSite
from models.job_zone import JobZone, JobZoneWorkingHours, JobZoneActivity
from models.organization import Organization
from models.activity_log import ActivityLog

# Import our new models (create the files later)
# GENIUS CORE CONTINUITY MODE models
from models.asset_location import AssetLocation
from models.driver_report import DriverReport
from models.pm_allocation import PMAllocation
from models.notification import Notification
from models.system_configuration import SystemConfiguration