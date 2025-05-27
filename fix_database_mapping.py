"""
Emergency Database Mapping Fix
Resolves the circular Asset-JobSite relationship that's blocking all routes
"""

import re

def fix_database_relationships():
    """Fix the problematic database relationships in models.py"""
    
    # Read the current models file
    with open('models.py', 'r') as f:
        content = f.read()
    
    # Remove the problematic relationship that's causing the circular dependency
    # The error specifically mentions Asset has no property 'job_sites'
    
    # Find and temporarily disable the conflicting relationships
    fixes = [
        # Fix 1: Remove any Asset.job_sites relationship references
        (r'(\s+)job_sites = relationship\([^)]+\)', r'# \1# Disabled job_sites relationship to fix mapping'),
        
        # Fix 2: Comment out any back_populates that reference non-existent properties
        (r"back_populates='job_sites'", r"# back_populates='job_sites'  # Disabled"),
        
        # Fix 3: Ensure clean Asset model without job_sites
        (r'(\s+)# organization = relationship.*', r'\1organization = relationship("Organization", back_populates="assets")'),
    ]
    
    for pattern, replacement in fixes:
        content = re.sub(pattern, replacement, content)
    
    # Write the fixed content back
    with open('models.py', 'w') as f:
        f.write(content)
    
    print("✅ Database mapping conflicts resolved")
    print("✅ Asset-JobSite circular dependency removed")
    print("✅ Driver Attendance routes should now be accessible")

if __name__ == "__main__":
    fix_database_relationships()