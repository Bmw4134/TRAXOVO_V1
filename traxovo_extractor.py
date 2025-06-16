#!/usr/bin/env python3
"""
TRAXOVO Deployment Extractor
Extracts and deploys TRAXOVO Intelligence Platform for client IT teams
"""

import os
import sys
import shutil
import json
import subprocess
from pathlib import Path

class TRAXOVOExtractor:
    def __init__(self):
        self.deployment_dir = "traxovo_deployed"
        self.required_files = [
            'main.py',
            'data_integration_real.py',
            'requirements.txt',
            'templates/',
            'static/',
            'setup_database.py'
        ]
    
    def extract_deployment(self):
        """Extract TRAXOVO system for deployment"""
        print("TRAXOVO Intelligence Platform Extractor")
        print("=====================================")
        
        # Create deployment directory
        if os.path.exists(self.deployment_dir):
            print(f"Removing existing deployment directory...")
            shutil.rmtree(self.deployment_dir)
        
        os.makedirs(self.deployment_dir)
        print(f"Created deployment directory: {self.deployment_dir}")
        
        # Copy system files
        self._copy_system_files()
        
        # Generate requirements.txt
        self._generate_requirements()
        
        # Generate setup script
        self._generate_setup_script()
        
        # Generate environment template
        self._generate_env_template()
        
        # Generate deployment readme
        self._generate_readme()
        
        print("\nDeployment extraction complete!")
        print(f"Files extracted to: {self.deployment_dir}/")
        print("\nNext steps:")
        print("1. cd traxovo_deployed")
        print("2. Copy .env.example to .env and configure")
        print("3. python setup_database.py")
        print("4. pip install -r requirements.txt")
        print("5. gunicorn --bind 0.0.0.0:5000 main:app")
    
    def _copy_system_files(self):
        """Copy essential system files"""
        files_to_copy = {
            'main.py': 'Application entry point',
            'data_integration_real.py': 'Data integration module',
            'templates/': 'HTML templates',
            'static/': 'CSS, JS, and assets'
        }
        
        for file_path, description in files_to_copy.items():
            src = file_path
            dst = os.path.join(self.deployment_dir, file_path)
            
            if os.path.isdir(src):
                shutil.copytree(src, dst)
                print(f"Copied directory: {file_path} ({description})")
            elif os.path.isfile(src):
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                shutil.copy2(src, dst)
                print(f"Copied file: {file_path} ({description})")
    
    def _generate_requirements(self):
        """Generate requirements.txt"""
        requirements = """Flask==2.3.3
Flask-SQLAlchemy==3.0.5
psycopg2-binary==2.9.7
gunicorn==21.2.0
python-dotenv==1.0.0
Werkzeug==2.3.7
"""
        
        req_path = os.path.join(self.deployment_dir, 'requirements.txt')
        with open(req_path, 'w') as f:
            f.write(requirements)
        print("Generated requirements.txt")
    
    def _generate_setup_script(self):
        """Generate database setup script"""
        setup_script = '''#!/usr/bin/env python3
"""
TRAXOVO Database Setup
Creates database tables and initial data
"""

import os
import psycopg2
from psycopg2.extras import RealDictCursor
import sys

def setup_database():
    """Setup TRAXOVO database"""
    db_url = os.environ.get('DATABASE_URL')
    if not db_url:
        print("ERROR: DATABASE_URL environment variable not set")
        print("Please set DATABASE_URL in your .env file")
        sys.exit(1)
    
    try:
        conn = psycopg2.connect(db_url)
        cursor = conn.cursor()
        
        print("Setting up TRAXOVO database tables...")
        
        # Users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                username VARCHAR(64) UNIQUE NOT NULL,
                email VARCHAR(120) UNIQUE NOT NULL,
                password_hash VARCHAR(256),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Assets table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS assets (
                id SERIAL PRIMARY KEY,
                asset_id VARCHAR(50) UNIQUE NOT NULL,
                name VARCHAR(100) NOT NULL,
                asset_type VARCHAR(50),
                location VARCHAR(100),
                latitude DECIMAL(10, 8),
                longitude DECIMAL(11, 8),
                status VARCHAR(20),
                hours_operated DECIMAL(10, 2),
                utilization DECIMAL(5, 2),
                last_maintenance TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                asset_metadata TEXT
            )
        """)
        
        # Attendance records table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS attendance_records (
                id SERIAL PRIMARY KEY,
                employee_id VARCHAR(50) NOT NULL,
                employee_name VARCHAR(100) NOT NULL,
                date DATE NOT NULL,
                clock_in TIMESTAMP,
                clock_out TIMESTAMP,
                hours_worked DECIMAL(5, 2),
                location VARCHAR(100),
                status VARCHAR(20),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Operational metrics table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS operational_metrics (
                id SERIAL PRIMARY KEY,
                metric_date DATE NOT NULL,
                total_assets INTEGER,
                active_assets INTEGER,
                fleet_utilization DECIMAL(5, 2),
                operational_hours DECIMAL(10, 2),
                efficiency_score DECIMAL(5, 2),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.commit()
        print("Database setup completed successfully!")
        
    except Exception as e:
        print(f"Database setup error: {e}")
        sys.exit(1)
    
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    setup_database()
'''
        
        setup_path = os.path.join(self.deployment_dir, 'setup_database.py')
        with open(setup_path, 'w') as f:
            f.write(setup_script)
        os.chmod(setup_path, 0o755)
        print("Generated setup_database.py")
    
    def _generate_env_template(self):
        """Generate environment template"""
        env_template = """# TRAXOVO Intelligence Platform Environment Configuration
# Copy this file to .env and configure your values

# Database Configuration (Required)
DATABASE_URL=postgresql://username:password@localhost/traxovo_db

# Session Security (Required - Generate a random 32+ character string)
SESSION_SECRET=your_32_character_random_secret_key_here

# Optional: OpenAI API for voice commands
OPENAI_API_KEY=sk-your-openai-key-here

# Application Settings
ENVIRONMENT=production
DEBUG=false
PORT=5000

# Example PostgreSQL URLs:
# Local: postgresql://postgres:password@localhost/traxovo
# Heroku: postgres://user:pass@host:port/database
# AWS RDS: postgresql://user:pass@rds-endpoint:5432/database
"""
        
        env_path = os.path.join(self.deployment_dir, '.env.example')
        with open(env_path, 'w') as f:
            f.write(env_template)
        print("Generated .env.example")
    
    def _generate_readme(self):
        """Generate deployment README"""
        readme = """# TRAXOVO Intelligence Platform Deployment

Enterprise equipment tracking and management system with real-time dashboard monitoring.

## Quick Start

1. **Configure Environment**
   ```bash
   cp .env.example .env
   # Edit .env with your database and configuration
   ```

2. **Setup Database**
   ```bash
   python setup_database.py
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Start Application**
   ```bash
   gunicorn --bind 0.0.0.0:5000 main:app
   ```

5. **Access System**
   - Open browser to http://localhost:5000
   - Login with first name as username and password
   - New users get automatic password reset and onboarding

## Default Accounts

- **admin**: Full system access
- **demo**: Demonstration account  
- **troy**: Executive dashboard access

## Features

- Real-time equipment tracking and monitoring
- Personnel management and attendance tracking
- Voice command integration
- Mobile responsive design
- Advanced authentication and security
- Live data visualization and reporting

## System Requirements

- Python 3.8+
- PostgreSQL 12+
- 2GB RAM minimum
- 10GB disk space

## Support

This is a deployment-only package. Basic deployment support available.
Contact your IT administrator for configuration assistance.

## Database Configuration

The system requires PostgreSQL. Update DATABASE_URL in .env file:

```
DATABASE_URL=postgresql://username:password@host:port/database
```

For production deployments, ensure proper database security and backups.
"""
        
        readme_path = os.path.join(self.deployment_dir, 'README.md')
        with open(readme_path, 'w') as f:
            f.write(readme)
        print("Generated README.md")

def main():
    """Main extraction function"""
    if len(sys.argv) > 1 and sys.argv[1] == '--deploy':
        extractor = TRAXOVOExtractor()
        extractor.extract_deployment()
    else:
        print("TRAXOVO Deployment Extractor")
        print("Usage: python traxovo_extractor.py --deploy")
        print("This will extract TRAXOVO system files for deployment")

if __name__ == "__main__":
    main()