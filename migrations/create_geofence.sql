-- Create geofence table if not exists
CREATE TABLE IF NOT EXISTS geofence (
    id SERIAL PRIMARY KEY,
    name VARCHAR(256) NOT NULL,
    latitude FLOAT NOT NULL,
    longitude FLOAT NOT NULL,
    radius FLOAT NOT NULL,
    type VARCHAR(16) DEFAULT 'static',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create an index on name
CREATE INDEX IF NOT EXISTS ix_geofence_name ON geofence (name);

-- Insert default geofences if none exist
INSERT INTO geofence (name, latitude, longitude, radius, type)
SELECT 'DFW Office', 32.9483, -96.7299, 500, 'static' 
WHERE NOT EXISTS (SELECT 1 FROM geofence LIMIT 1);

INSERT INTO geofence (name, latitude, longitude, radius, type)
SELECT 'Houston Office', 29.7604, -95.3698, 500, 'static'
WHERE NOT EXISTS (SELECT 1 FROM geofence WHERE id = 1);

INSERT INTO geofence (name, latitude, longitude, radius, type)
SELECT 'West Texas Office', 31.9686, -102.0878, 500, 'static'
WHERE NOT EXISTS (SELECT 1 FROM geofence WHERE id = 2);