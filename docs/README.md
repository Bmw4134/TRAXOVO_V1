# TRAXOVO Watson Intelligence Platform

Advanced autonomous system intelligence platform with sophisticated Watson Command Console, designed for intelligent enterprise-level AI system management and distributed computational analysis.

## Features

- **Watson Command Console**: Proprietary command interface for AI system management
- **Real-time Dashboard**: Live monitoring and analytics
- **Secure Authentication**: Multi-level access control system
- **Enterprise Analytics**: Advanced fleet and operational insights
- **Mobile Optimized**: Responsive design for all devices
- **PostgreSQL Integration**: Robust data persistence layer

## Technology Stack

- **Backend**: Flask with Python 3.11
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Frontend**: Modern JavaScript with responsive CSS
- **Authentication**: Flask-Login with session management
- **Deployment**: Gunicorn WSGI server
- **Infrastructure**: Replit Cloud with auto-scaling

## Installation

### Development Setup

```bash
# Clone the repository
git clone https://github.com/traxovo/watson-intelligence.git
cd watson-intelligence

# Install dependencies
pip install -e .

# Set environment variables
export SESSION_SECRET="your-secret-key"
export DATABASE_URL="your-postgresql-url"

# Run the application
python main.py
```

### Production Deployment

The application is optimized for Replit deployment with automatic dependency management through `pyproject.toml`.

## Configuration

### Environment Variables

- `SESSION_SECRET`: Flask session secret key
- `DATABASE_URL`: PostgreSQL connection string
- `PORT`: Application port (default: 5000)

### User Authentication

Default users:
- **Watson**: Supreme Intelligence (Access Level 11)
- **Demo**: Standard operator (Access Level 5)

## API Endpoints

- `GET /` - Landing page
- `POST /login` - Authentication
- `GET /dashboard` - Main dashboard
- `GET /logout` - Session termination
- `GET /api/status` - System status
- `GET /health` - Health check

## Architecture

### Core Components

1. **Main Application** (`main.py`): Flask application entry point
2. **Database Models** (`models.py`): SQLAlchemy ORM definitions
3. **Static Assets** (`static/`): JavaScript modules and CSS
4. **Templates** (`templates/`): Jinja2 HTML templates

### JavaScript Modules

- **Dashboard Analytics**: Real-time metrics and visualization
- **Enterprise Sidebar**: Unified navigation system
- **Mobile Optimization**: Touch-friendly responsive design
- **Performance Engine**: Intelligent caching and optimization
- **Voice Commands**: Natural language interface
- **PDF Export**: Professional report generation

## Security

- Session-based authentication
- CSRF protection
- Secure password handling
- Environment-based configuration
- Production-ready security headers

## Performance

- Optimized database queries
- Intelligent client-side caching
- Lazy loading for non-critical resources
- Mobile-first responsive design
- CDN-ready static assets

## License

MIT License - See LICENSE file for details

## Support

For enterprise support and custom implementations, contact the TRAXOVO Intelligence team.