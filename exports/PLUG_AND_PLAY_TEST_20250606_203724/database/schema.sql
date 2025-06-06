
            -- NEXUS Database Schema Export
            -- Generated: 2025-06-06T20:37:24.527661
            
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username VARCHAR(64) UNIQUE NOT NULL,
                email VARCHAR(120) UNIQUE NOT NULL,
                password_hash VARCHAR(256),
                role VARCHAR(32) DEFAULT 'user',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT 1
            );
            
            CREATE TABLE IF NOT EXISTS platform_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                data_type VARCHAR(50) NOT NULL,
                data_content JSON,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );
            
            CREATE TABLE IF NOT EXISTS trading_signals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticker VARCHAR(10) NOT NULL,
                signal_type VARCHAR(20) NOT NULL,
                entry_price DECIMAL(10,2),
                exit_target DECIMAL(10,2),
                stop_loss DECIMAL(10,2),
                confidence_score INTEGER,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );
            
            CREATE TABLE IF NOT EXISTS automation_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id VARCHAR(100),
                request_type VARCHAR(50),
                request_data JSON,
                status VARCHAR(20) DEFAULT 'pending',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );
            