#!/bin/bash
# NEXUS Multi-Port Startup Script

echo "Starting NEXUS Enterprise Multi-Port Configuration..."

# Start primary server on port 5000
gunicorn --config gunicorn_port_5000.conf.py app_executive:app &
echo "Primary server started on port 5000"

# Start additional servers
gunicorn --config gunicorn_port_5001.conf.py app_executive:app &
echo "Additional server started on port 5001"

gunicorn --config gunicorn_port_5002.conf.py app_executive:app &
echo "Additional server started on port 5002"

gunicorn --config gunicorn_port_5003.conf.py app_executive:app &
echo "Additional server started on port 5003"

gunicorn --config gunicorn_port_5004.conf.py app_executive:app &
echo "Additional server started on port 5004"

# Wait for servers to initialize
sleep 5

# Start Nginx load balancer (if available)
if command -v nginx &> /dev/null; then
    nginx -c $(pwd)/nginx_nexus.conf
    echo "Load balancer started on port 8080"
else
    echo "Nginx not available - using direct multi-port access"
fi

echo "NEXUS Multi-Port Configuration Active"
echo "Primary Access: http://localhost:5000"
echo "Load Balanced: http://localhost:8080"
echo "Direct Ports: 5000, 5001, 5002, 5003, 5004"
