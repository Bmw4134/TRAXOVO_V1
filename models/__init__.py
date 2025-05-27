# Essential models for TRAXOVO login system
from models.user import User
from models.asset import Asset
from models.driver import Driver
from models.activity_log import ActivityLog
from models.driver_report import DriverReport
from models.system_configuration import SystemConfiguration

# Required models for routes
from models.pm_allocation import PMAllocation
from models.job_site import JobSite
from models.organization import Organization
from models.notification import Notification
from models.asset_location import AssetLocation